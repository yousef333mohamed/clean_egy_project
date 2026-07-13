"""Stable database evidence and numeric/null preservation."""

from decimal import Decimal

from app.analytics.evidence_builder import EvidenceBuilder
from app.schemas.analytics_tools import AnalyticsToolResult


def test_evidence_ids_values_period_and_no_sql():
    results = [
        AnalyticsToolResult(
            tool_name="safe",
            metric="count",
            description="Evidence",
            columns=["value", "missing"],
            rows=[{"value": Decimal("42.5"), "missing": None}],
            filters={"region": "Delta"},
            notes=["Historical."],
        )
    ]
    evidence = EvidenceBuilder().build(results)[0]
    assert evidence.evidence_id == "D1"
    assert evidence.rows == [{"value": 42.5, "missing": None}]
    assert "sql" not in evidence.model_dump()


def test_multiple_results_have_stable_ids():
    result = AnalyticsToolResult(tool_name="safe", description="x", columns=[], rows=[], filters={})
    assert [item.evidence_id for item in EvidenceBuilder().build([result, result])] == ["D1", "D2"]
