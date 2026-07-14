"""Rules-first routing and LLM-output validation."""

import pytest

from app.analytics.enums import AnalyticsRoute
from app.analytics.tool_registry import build_tool_registry
from app.services.analytics_router_service import AnalyticsRouterService


@pytest.fixture
def router(analytics_settings):
    return AnalyticsRouterService(build_tool_registry(analytics_settings), analytics_settings)


@pytest.mark.parametrize(
    ("question", "route", "tool"),
    [
        ("Which region had the most missed collections in March 2026?", AnalyticsRoute.STRUCTURED_DATA, "rank_regions_by_operations_metric"),
        ("What is the complaint escalation procedure?", AnalyticsRoute.DOCUMENT_KNOWLEDGE, None),
        ("Which region had the most complaints, and what procedure applies?", AnalyticsRoute.HYBRID_ANALYSIS, "rank_regions_by_operations_metric"),
        ("Which bins will overflow tomorrow?", AnalyticsRoute.UNSUPPORTED, None),
        ("Which bins should receive manager attention first?", AnalyticsRoute.STRUCTURED_DATA, "list_critical_bins"),
        ("Delete all trip records", AnalyticsRoute.UNSUPPORTED, None),
        ("ما هي المنطقة التي سجلت أكبر عدد من عمليات الجمع الفائتة في مارس 2026؟", AnalyticsRoute.STRUCTURED_DATA, "rank_regions_by_operations_metric"),
    ],
)
async def test_deterministic_routes(router, question, route, tool):
    result = await router.route(question)
    assert result.route == route and result.tool_name == tool


async def test_mixed_language_region_preserved(router):
    result = await router.route("اعرض أداء الشاحنات في Greater Cairo خلال last 30 days")
    assert result.parameters.region == "Greater Cairo"
    assert result.parameters.start_date.isoformat() == "2026-06-14"


async def test_unknown_llm_tool_rejected(analytics_settings):
    class LLM:
        async def route_analytics(self, **_kwargs):
            return {"route": "STRUCTURED_DATA", "tool_name": "run_sql", "parameters": {}}

    service = AnalyticsRouterService(build_tool_registry(analytics_settings), analytics_settings, llm_service=LLM())
    result = await service.route("Tell me something obscure")
    assert result.route == AnalyticsRoute.UNSUPPORTED


async def test_llm_failure_falls_back_safely(analytics_settings):
    class LLM:
        async def route_analytics(self, **_kwargs):
            raise RuntimeError("offline")

    result = await AnalyticsRouterService(build_tool_registry(analytics_settings), analytics_settings, llm_service=LLM()).route("ambiguous")
    assert result.route == AnalyticsRoute.UNSUPPORTED


async def test_impossible_date_does_not_execute_without_filter(router):
    result = await router.route("complaints from 2026-02-30 to 2026-03-01")
    assert result.route == AnalyticsRoute.UNSUPPORTED
