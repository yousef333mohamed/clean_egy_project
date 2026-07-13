"""Bounded-concurrency deterministic evaluation runner."""

import asyncio
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.evaluation.analytics_evaluator import AnalyticsEvaluator
from app.evaluation.case_loader import CaseLoader
from app.evaluation.decision_evaluator import DecisionEvaluator
from app.evaluation.enums import EvaluationMode
from app.evaluation.evaluators import SafetyEvaluator
from app.evaluation.quality_gate import QualityGate
from app.evaluation.rag_evaluator import RAGEvaluator
from app.evaluation.reports import write_reports
from app.evaluation.retrieval_evaluator import RetrievalEvaluator
from app.models.evaluation_result import EvaluationResult
from app.models.evaluation_run import EvaluationRun, EvaluationRunStatus
from app.observability.sanitization import sanitize, sanitize_text
from app.schemas.evaluation import EvaluationActualResult, EvaluationCaseResult, EvaluationRunResult


class RegressionRunner:
    def __init__(self, session: Any | None = None, settings: Settings | None = None, *, actual_provider: Any | None = None, write_report_files: bool = True) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.actual_provider = actual_provider
        self.write_report_files = write_report_files

    async def run(self, dataset_path: Path, *, mode: EvaluationMode = EvaluationMode.FAKE_PROVIDERS, prompt_overrides: dict[str, str] | None = None) -> EvaluationRunResult:
        if mode == EvaluationMode.LIVE_PROVIDERS and not self.settings.evaluation_allow_live_providers:
            raise ValueError("Live-provider evaluation is disabled")
        dataset = CaseLoader().load(dataset_path)
        started = time.perf_counter()
        run = EvaluationRunResult(
            name=f"{dataset.name}-{datetime.now(UTC).isoformat()}", evaluation_type=dataset.evaluation_type, dataset_name=dataset.name,
            dataset_version=dataset.version, mode=mode, prompt_versions=prompt_overrides or {},
            model_configuration={"provider_mode": mode.value, "live_providers": mode == EvaluationMode.LIVE_PROVIDERS},
        )
        db_run = None
        if self.session is not None:
            db_run = EvaluationRun(id=run.run_id, name=run.name, evaluation_type=run.evaluation_type, status=EvaluationRunStatus.RUNNING, dataset_name=run.dataset_name,
                dataset_version=run.dataset_version, prompt_versions_json=run.prompt_versions, model_configuration_json=run.model_configuration, started_at=datetime.now(UTC))
            self.session.add(db_run)
            await self.session.flush()
        semaphore = asyncio.Semaphore(self.settings.evaluation_max_concurrency)

        async def execute(case):
            async with semaphore:
                return await asyncio.wait_for(self._evaluate_case(dataset.evaluation_type, case, mode), timeout=self.settings.evaluation_timeout_seconds)

        for batch_start in range(0, len(dataset.cases), self.settings.evaluation_max_concurrency):
            outcomes = await asyncio.gather(*(execute(case) for case in dataset.cases[batch_start:batch_start + self.settings.evaluation_max_concurrency]), return_exceptions=True)
            for case, outcome in zip(dataset.cases[batch_start:batch_start + self.settings.evaluation_max_concurrency], outcomes, strict=True):
                if isinstance(outcome, BaseException):
                    outcome = EvaluationCaseResult(case_id=case.case_id, category=case.category, passed=False, score=0, failure_reasons=[f"Evaluation error: {type(outcome).__name__}"], duration_ms=0, language=case.language)
                run.results.append(outcome)
                if outcome.critical_failure:
                    break
            if any(result.critical_failure for result in run.results):
                break
        run.critical_failures = sum(result.critical_failure for result in run.results)
        run.duration_ms = (time.perf_counter() - started) * 1000
        run.metrics = self._aggregate(run.results)
        if db_run is not None:
            for case, result in zip(dataset.cases, run.results, strict=False):
                self.session.add(EvaluationResult(evaluation_run_id=run.run_id, case_id=case.case_id, category=case.category, status="PASSED" if result.passed else "FAILED",
                    question=sanitize_text(case.question, max_length=1000), expected_json=sanitize(case.model_dump(mode="json", exclude={"question", "recorded_response"})), actual_json={},
                    metrics_json=result.metrics, warnings_json=result.warnings, failure_reasons_json=result.failure_reasons, duration_ms=result.duration_ms))
            db_run.status = EvaluationRunStatus.STOPPED_CRITICAL if run.critical_failures else EvaluationRunStatus.COMPLETED
            db_run.completed_at = datetime.now(UTC)
            db_run.total_cases = len(run.results)
            db_run.passed_cases = sum(result.passed for result in run.results)
            db_run.failed_cases = len(run.results) - db_run.passed_cases
            db_run.critical_failures = run.critical_failures
            db_run.metrics_json = run.metrics
            await self.session.commit()
        gate = QualityGate(self.settings).evaluate(run.metrics, total_cases=len(run.results), critical_failures=run.critical_failures)
        if self.write_report_files:
            write_reports(run, gate)
        return run

    async def _evaluate_case(self, evaluation_type, case, mode):
        started = time.perf_counter()
        actual = await self._actual(case, mode)
        evaluator = self._evaluator(evaluation_type)
        result = await evaluator.evaluate(case, actual)
        return EvaluationCaseResult(case_id=case.case_id, category=case.category, passed=result.passed, score=result.score, metrics=result.metrics,
            failure_reasons=result.failure_reasons, warnings=result.warnings, critical_failure=result.critical, duration_ms=(time.perf_counter() - started) * 1000, language=case.language)

    async def _actual(self, case, mode):
        if self.actual_provider is not None:
            value = await self.actual_provider(case, mode)
            return value if isinstance(value, EvaluationActualResult) else EvaluationActualResult.model_validate(value)
        payload = case.recorded_response or case.expected.get("actual") or self._fake_from_expected(case)
        return EvaluationActualResult.model_validate(payload)

    @staticmethod
    def _fake_from_expected(case):
        expected = case.expected
        return {"route": case.expected_route, "tool": case.expected_tool, "retrieved_documents": case.expected_documents,
            "citations": expected.get("citations", []), "supplied_source_ids": expected.get("supplied_source_ids", []), "answer": expected.get("answer", " ".join(case.expected_concepts)),
            "insufficient_context": case.expected_insufficient_context, "decision_type": expected.get("decision_type", case.expected_route),
            "action_category": (expected.get("allowed_action_categories") or [None])[0], "required_tools": expected.get("required_tools", []),
            "evidence_ids": expected.get("evidence_ids", ["E1"] if expected.get("requires_evidence") else []), "requires_human_approval": case.expected_human_approval,
            "scores": expected.get("scores", {}), "confidence": expected.get("confidence"),
            "missing_information": expected.get("missing_information", ["unavailable"] if expected.get("requires_missing_information") else []),
            "expected_numeric_values": expected.get("numeric_values", []), "numeric_values": expected.get("numeric_values", []), "filters": expected.get("filters", {}),
            "date_range": expected.get("date_range", {}), "domain": expected.get("domain"), "metrics": expected.get("metrics", [])}

    @staticmethod
    def _evaluator(evaluation_type):
        lowered = evaluation_type.casefold()
        if "retrieval" in lowered:
            return RetrievalEvaluator()
        if "analytics" in lowered:
            return AnalyticsEvaluator()
        if "decision" in lowered:
            return DecisionEvaluator()
        if "safety" in lowered:
            return SafetyEvaluator()
        return RAGEvaluator()

    @staticmethod
    def _aggregate(results):
        values = defaultdict(list)
        for result in results:
            for key, value in result.metrics.items():
                if isinstance(value, (int, float)):
                    values[key].append(float(value))
        return {key: sum(items) / len(items) for key, items in values.items()}
