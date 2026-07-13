"""Dataset discovery, persisted-run access, and comparison orchestration."""

from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.evaluation.regression_runner import RegressionRunner
from app.models.evaluation_result import EvaluationResult
from app.models.evaluation_run import EvaluationRun

DATASET_ROOT = Path(__file__).resolve().parents[2] / "evaluation_datasets"


class EvaluationService:
    def __init__(self, session: Any, settings=None) -> None:
        self.session = session
        self.settings = settings

    def datasets(self) -> list[dict[str, str]]:
        return [{"name": path.stem, "type": path.parent.name, "path": str(path.relative_to(DATASET_ROOT)), "version": "1.0.0"} for path in sorted(DATASET_ROOT.glob("*/*.json"))]

    def resolve_dataset(self, name: str) -> Path:
        safe = Path(name).name
        candidates = list(DATASET_ROOT.glob(f"*/{safe}" if safe.endswith(".json") else f"*/{safe}.json"))
        if len(candidates) != 1:
            raise ValueError("Unknown evaluation dataset")
        return candidates[0]

    async def start(self, name: str, mode, prompt_overrides=None):
        return await RegressionRunner(self.session, self.settings).run(self.resolve_dataset(name), mode=mode, prompt_overrides=prompt_overrides)

    async def get_run(self, run_id: UUID):
        return (await self.session.execute(select(EvaluationRun).where(EvaluationRun.id == run_id))).scalar_one_or_none()

    async def get_results(self, run_id: UUID):
        return list((await self.session.execute(select(EvaluationResult).where(EvaluationResult.evaluation_run_id == run_id).order_by(EvaluationResult.created_at))).scalars())

    async def compare(self, baseline_id: UUID, candidate_id: UUID) -> dict:
        baseline, candidate = await self.get_run(baseline_id), await self.get_run(candidate_id)
        if baseline is None or candidate is None:
            raise ValueError("Evaluation run not found")
        keys = set(baseline.metrics_json) | set(candidate.metrics_json)
        deltas = {key: float(candidate.metrics_json.get(key, 0)) - float(baseline.metrics_json.get(key, 0)) for key in keys}
        baseline_results = {item.case_id: item.status for item in await self.get_results(baseline_id)}
        candidate_results = {item.case_id: item.status for item in await self.get_results(candidate_id)}
        return {"baseline": str(baseline_id), "candidate": str(candidate_id), "metric_deltas": deltas,
            "improvements": sorted(key for key, value in deltas.items() if value > 0), "regressions": sorted(key for key, value in deltas.items() if value < 0),
            "newly_failing_cases": sorted(key for key, value in candidate_results.items() if value == "FAILED" and baseline_results.get(key) == "PASSED"),
            "newly_passing_cases": sorted(key for key, value in candidate_results.items() if value == "PASSED" and baseline_results.get(key) == "FAILED"),
            "critical_failure_delta": candidate.critical_failures - baseline.critical_failures}
