"""Credential-safe JSON and Markdown evaluation reports."""

import json
from collections import defaultdict
from pathlib import Path

from app.observability.sanitization import sanitize
from app.schemas.evaluation import EvaluationRunResult, QualityGateResult


def report_payload(run: EvaluationRunResult, gate: QualityGateResult) -> dict:
    categories: dict[str, list[bool]] = defaultdict(list)
    languages: dict[str, list[bool]] = defaultdict(list)
    for result in run.results:
        categories[result.category].append(result.passed)
        languages[result.language].append(result.passed)
    return sanitize(
        {
            "run": {
                "id": str(run.run_id),
                "name": run.name,
                "evaluation_type": run.evaluation_type,
                "dataset": run.dataset_name,
                "dataset_version": run.dataset_version,
                "mode": run.mode.value,
            },
            "prompt_versions": run.prompt_versions,
            "model_configuration": run.model_configuration,
            "metrics": run.metrics,
            "quality_gate": gate.model_dump(mode="json"),
            "critical_failures": run.critical_failures,
            "failed_cases": [result.model_dump(mode="json") for result in run.results if not result.passed],
            "category_results": {key: {"passed": sum(values), "total": len(values)} for key, values in categories.items()},
            "language_results": {key: {"passed": sum(values), "total": len(values)} for key, values in languages.items()},
            "latency": {"total_ms": run.duration_ms, "mean_case_ms": run.duration_ms / len(run.results) if run.results else 0},
            "warnings": sorted({warning for result in run.results for warning in result.warnings}),
        }
    )


def write_reports(run: EvaluationRunResult, gate: QualityGateResult, directory: Path = Path("evaluation_reports")) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    payload = report_payload(run, gate)
    json_path = directory / f"{run.run_id}.json"
    markdown_path = directory / f"{run.run_id}.md"
    if json_path.exists() or markdown_path.exists():
        raise FileExistsError("Evaluation reports are immutable; destination already exists")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    gate_text = "PASS" if gate.passed else "FAIL"
    failed = "\n".join(f"- {item['case_id']}: {', '.join(item['failure_reasons'])}" for item in payload["failed_cases"]) or "- None"
    metric_lines = "\n".join(f"- {key}: {value}" for key, value in run.metrics.items())
    markdown_path.write_text(
        f"# Evaluation {run.run_id}\n\nDataset: `{run.dataset_name}` version `{run.dataset_version}`\n\nQuality gate: **{gate_text}**\n\n## Metrics\n\n{metric_lines}\n\n## Failed cases\n\n{failed}\n",
        encoding="utf-8",
    )
    return json_path, markdown_path
