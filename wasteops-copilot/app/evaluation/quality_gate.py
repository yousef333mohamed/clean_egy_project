"""Deterministic release quality gate."""

from app.core.config import Settings, get_settings
from app.schemas.evaluation import QualityGateFailure, QualityGateResult


class QualityGate:
    REQUIRED_METRICS = ("retrieval_recall_at_5", "citation_validity", "route_accuracy", "tool_accuracy", "groundedness", "numeric_error_rate")

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def evaluate(self, metrics: dict[str, float], *, total_cases: int, critical_failures: int = 0) -> QualityGateResult:
        rules = {
            "retrieval_recall_at_5": (">=", self.settings.quality_gate_min_retrieval_recall),
            "citation_validity": (">=", self.settings.quality_gate_min_citation_validity),
            "route_accuracy": (">=", self.settings.quality_gate_min_route_accuracy),
            "tool_accuracy": (">=", self.settings.quality_gate_min_tool_accuracy),
            "groundedness": (">=", self.settings.quality_gate_min_groundedness),
            "numeric_error_rate": ("<=", self.settings.quality_gate_max_numeric_error_rate),
        }
        failures: list[QualityGateFailure] = []
        if total_cases <= 0:
            failures.append(QualityGateFailure(metric="total_cases", required="> 0", actual=total_cases))
        for metric, (operator, required) in rules.items():
            actual = metrics.get(metric)
            if actual is None or (operator == ">=" and actual < required) or (operator == "<=" and actual > required):
                failures.append(QualityGateFailure(metric=metric, required=required, actual=actual))
        if critical_failures > self.settings.quality_gate_max_critical_failures:
            failures.append(QualityGateFailure(metric="critical_failures", required=self.settings.quality_gate_max_critical_failures, actual=critical_failures))
        return QualityGateResult(passed=not failures, metrics=metrics, failed_rules=failures, critical_failures=critical_failures)
