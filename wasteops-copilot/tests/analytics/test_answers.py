"""Structured answer grounding and citation validation."""

from app.analytics.evidence_builder import EvidenceBuilder
from app.analytics.enums import AnalyticsDomain, AnalyticsRoute
from app.schemas.analytics import AnalyticsRouteDecision
from app.schemas.analytics_tools import AnalyticsToolResult
from app.services.analytics_answer_service import AnalyticsAnswerService


class FakeLLM:
    def __init__(self, answer):
        self.answer = answer

    async def generate_grounded_answer(self, **_kwargs):
        return self.answer


def evidence(rows):
    return EvidenceBuilder().build(
        [
            AnalyticsToolResult(
                tool_name="get_operations_summary",
                description="March counts",
                columns=list(rows[0]) if rows else [],
                rows=rows,
                filters={"start_date": "2026-03-01", "end_date": "2026-03-31"},
            )
        ]
    )[0]


def decision():
    return AnalyticsRouteDecision(route=AnalyticsRoute.STRUCTURED_DATA, domain=AnalyticsDomain.OPERATIONS, tool_name="get_operations_summary")


async def test_structured_grounded_answer_preserves_database_number():
    response = await AnalyticsAnswerService(FakeLLM("There were 42 missed collections in March 2026. [D1]")).answer(
        question="How many?", decision=decision(), evidence=evidence([{"missed_collection_count": 42, "records_included": 50}])
    )
    assert "42" in response.answer and response.citations[0].citation_id == "D1"


async def test_invalid_database_citation_removed():
    response = await AnalyticsAnswerService(FakeLLM("Answer [D9]")).answer(
        question="How many?", decision=decision(), evidence=evidence([{"records_included": 1}])
    )
    assert "[D9]" not in response.answer and not response.grounded


async def test_no_data_does_not_call_provider():
    response = await AnalyticsAnswerService(None).answer(question="How many?", decision=decision(), evidence=evidence([{"records_included": 0}]))
    assert response.insufficient_data and "No matching" in response.answer
