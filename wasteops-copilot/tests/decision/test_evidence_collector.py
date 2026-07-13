"""D/S/R evidence collection, quality warnings, and provider failures."""

from datetime import UTC, datetime

import pytest

from app.decision.enums import DecisionType
from app.decision.evidence_collector import DecisionEvidenceCollector
from app.retrieval.context_builder import ContextBuilder
from app.schemas.decision import DecisionRequest
from app.schemas.decision_context import DecisionContextPlan, PlannedAnalyticsCall, PlannedDocumentQuery
from app.schemas.operational_evidence import DataPeriod, OperationalEvidence
from app.schemas.retrieval import RetrievalResponse, RetrievedEvidence
from app.utils.token_counter import TokenCounter


class Analytics:
    def __init__(self, rows=None):
        self.rows = rows if rows is not None else [{"records_included": 3, "missed_collection_count": 2}]

    async def execute(self, tool, _params, _session):
        return OperationalEvidence(
            evidence_id="D1",
            tool_name=tool,
            description="Operational facts",
            filters={},
            columns=list(self.rows[0]) if self.rows else [],
            rows=self.rows,
            record_count=len(self.rows),
            data_period=DataPeriod(start="2026-03-01", end="2026-03-31"),
            generated_at=datetime.now(UTC),
            notes=["records_missing_completion_time: 1"] if self.rows else [],
        )


class Retrieval:
    def __init__(self, evidence=None, error=None):
        self.evidence = evidence or []
        self.error = error

    async def search(self, request):
        if self.error:
            raise self.error
        return RetrievalResponse(query=request.query, rewritten_query=None, language="en", evidence=self.evidence, filters_applied={})


def document(synthetic=True, authority="demo_only"):
    return RetrievedEvidence(
        chunk_id="c1",
        document_id="doc1",
        source_filename="sop.md",
        document_title="Demo SOP",
        document_type="incident_procedure",
        language="en",
        chunk_number=0,
        content="Review the incident and require manager approval.",
        content_preview="Review the incident.",
        final_score=0.9,
        is_synthetic=synthetic,
        authority_level=authority,
    )


def plan(with_documents=True):
    return DecisionContextPlan(
        decision_type=DecisionType.MISSED_COLLECTION_RESPONSE,
        analytics_calls=[PlannedAnalyticsCall(tool="get_operations_summary")],
        document_queries=[PlannedDocumentQuery(query="procedure")] if with_documents else [],
        required_evidence_categories=["operations_outcomes", "response_guidance"],
    )


async def collect(settings, analytics, retrieval, selected_plan=None):
    return await DecisionEvidenceCollector(analytics, retrieval, ContextBuilder(TokenCounter(settings.chat_model_name)), object(), settings).collect(
        DecisionRequest(question="missed collections"), selected_plan or plan()
    )


async def test_collects_database_document_and_rule_namespaces(decision_settings):
    result = await collect(decision_settings, Analytics(), Retrieval([document()]))
    ids = {item.evidence_id for item in result.evidence}
    assert "D1" in ids and "S1" in ids
    assert all(not identifier.startswith("M") for identifier in ids)
    assert result.database_evidence and result.document_citations


async def test_synthetic_and_unknown_authority_warnings(decision_settings):
    result = await collect(decision_settings, Analytics(), Retrieval([document(synthetic=True, authority="unknown")]))
    assert any("synthetic" in warning.casefold() for warning in result.warnings)
    assert any("unknown authority" in warning.casefold() for warning in result.warnings)


async def test_empty_analytics_is_marked_no_data(decision_settings):
    result = await collect(decision_settings, Analytics([]), Retrieval(), plan(with_documents=False))
    database = next(item for item in result.evidence if item.evidence_id == "D1")
    assert database.supporting_values["has_data"] is False
    assert any("No matching" in warning for warning in result.warnings)


async def test_provider_failure_is_not_converted_to_model_evidence(decision_settings):
    with pytest.raises(RuntimeError):
        await collect(decision_settings, Analytics(), Retrieval(error=RuntimeError("offline")))


async def test_configured_rules_use_r_namespace(decision_settings):
    bin_plan = DecisionContextPlan(
        decision_type=DecisionType.BIN_ATTENTION_PRIORITY,
        analytics_calls=[PlannedAnalyticsCall(tool="list_critical_bins")],
        document_queries=[],
        required_evidence_categories=["latest_bin_status", "configured_rules"],
    )
    result = await collect(decision_settings, Analytics([{"bin_id": "BIN-1"}]), Retrieval(), bin_plan)
    assert {item.evidence_id for item in result.evidence} >= {"D1", "R1", "R2", "R3"}
    assert not any(item.evidence_id.startswith("M") for item in result.evidence)
