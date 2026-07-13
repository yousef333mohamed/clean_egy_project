"""Deterministic release-gate coverage."""

from app.core.config import Settings
from app.evaluation.quality_gate import QualityGate


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://x:x@db/x", "database_sync_url": "postgresql+psycopg://x:x@db/x"}
    values.update(updates)
    return Settings(**values)


def passing_metrics():
    return {"retrieval_recall_at_5": 1, "citation_validity": 1, "route_accuracy": 1, "tool_accuracy": 1, "groundedness": 1, "numeric_error_rate": 0}


def test_gate_passes_deterministically():
    assert QualityGate(settings()).evaluate(passing_metrics(), total_cases=4).passed


def test_gate_fails_missing_metric_empty_and_critical():
    gate = QualityGate(settings())
    assert not gate.evaluate({}, total_cases=0).passed
    assert not gate.evaluate(passing_metrics(), total_cases=1, critical_failures=1).passed


def test_gate_rejects_numeric_change():
    metrics = passing_metrics()
    metrics["numeric_error_rate"] = 0.01
    result = QualityGate(settings()).evaluate(metrics, total_cases=1)
    assert not result.passed and any(item.metric == "numeric_error_rate" for item in result.failed_rules)
