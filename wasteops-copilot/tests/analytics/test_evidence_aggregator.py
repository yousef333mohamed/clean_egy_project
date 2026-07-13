"""Database/document namespace separation and token limits."""

from app.analytics.evidence_builder import EvidenceBuilder
from app.retrieval.evidence_aggregator import EvidenceAggregator
from app.schemas.analytics_tools import AnalyticsToolResult


class Counter:
    def count(self, text):
        return len(text.split())


def test_database_precedes_documents_and_ids_do_not_collide():
    evidence = EvidenceBuilder().build([AnalyticsToolResult(tool_name="safe", description="facts", columns=["count"], rows=[{"count": 2}], filters={})])
    text, warnings = EvidenceAggregator(Counter()).aggregate(evidence, "[S1] procedure", max_tokens=100)
    assert text.index("D1") < text.index("[S1]")
    assert not warnings


def test_policy_first_and_budget_enforced():
    evidence = EvidenceBuilder().build([AnalyticsToolResult(tool_name="safe", description="facts", columns=[], rows=[], filters={})])
    text, warnings = EvidenceAggregator(Counter()).aggregate(evidence, "[S1] " + "word " * 100, max_tokens=20, policy_first=True)
    assert text.startswith("DOCUMENT EVIDENCE")
    assert len(text.split()) <= 20 and warnings
