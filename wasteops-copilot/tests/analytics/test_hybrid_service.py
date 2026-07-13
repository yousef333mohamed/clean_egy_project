"""Unsupported hybrid path is safe and dependency-free."""

from app.analytics.enums import AnalyticsRoute
from app.schemas.analytics import AnalyticsRouteDecision
from app.schemas.hybrid_answer import HybridQuestionRequest
from app.services.hybrid_intelligence_service import HybridIntelligenceService


class Router:
    async def route(self, _question):
        return AnalyticsRouteDecision(route=AnalyticsRoute.UNSUPPORTED, unsupported_reason="Future prediction required.")


async def test_unsupported_prediction_executes_no_tools():
    service = HybridIntelligenceService(Router(), None, None, None, None, None, None, None, None, None)
    response = await service.answer(HybridQuestionRequest(question="Predict overflow tomorrow"))
    assert response.route == AnalyticsRoute.UNSUPPORTED
    assert not response.grounded and "No arbitrary SQL" in response.answer


async def test_general_conversation_executes_no_tools():
    class GeneralRouter:
        async def route(self, _question):
            return AnalyticsRouteDecision(route=AnalyticsRoute.GENERAL_CONVERSATION)

    service = HybridIntelligenceService(GeneralRouter(), None, None, None, None, None, None, None, None, None)
    response = await service.answer(HybridQuestionRequest(question="Hello"))
    assert response.route == AnalyticsRoute.GENERAL_CONVERSATION and not response.database_evidence
