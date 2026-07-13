"""Minimal allow-listed decision context planning."""

from datetime import date

from app.decision.context_planner import DecisionContextPlanner
from app.decision.decision_router import DecisionRouter
from app.schemas.decision import DecisionRequest, DecisionScope


async def make_plan(question, decision_registry, analytics_registry, settings, scope=None):
    request = DecisionRequest(question=question, scope=scope or DecisionScope())
    route = await DecisionRouter(decision_registry, analytics_registry).route(request)
    return DecisionContextPlanner(decision_registry, analytics_registry, settings).plan(request, route)


async def test_truck_id_and_latest_data_propagate(decision_registry, analytics_registry, decision_settings):
    plan = await make_plan("Should TRK-014 be inspected?", decision_registry, analytics_registry, decision_settings)
    assert all(call.parameters["truck_id"] == "TRK-014" for call in plan.analytics_calls)
    assert all(call.parameters["latest_available"] is True for call in plan.analytics_calls)


async def test_region_and_explicit_dates_propagate(decision_registry, analytics_registry, decision_settings):
    scope = DecisionScope(region="Greater Cairo", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31), use_latest_available_data=False)
    plan = await make_plan("missed collections", decision_registry, analytics_registry, decision_settings, scope)
    assert all(call.parameters.get("region") == "Greater Cairo" for call in plan.analytics_calls)
    assert all(call.parameters.get("start_date") == date(2026, 3, 1) for call in plan.analytics_calls)


async def test_document_query_and_expected_categories(decision_registry, analytics_registry, decision_settings):
    plan = await make_plan("sensor maintenance response", decision_registry, analytics_registry, decision_settings)
    assert plan.document_queries and "maintenance" in plan.document_queries[0].query
    assert "latest_sensor_status" in plan.required_evidence_categories


async def test_unsupported_has_no_calls(decision_registry, analytics_registry, decision_settings):
    plan = await make_plan("Which bins will overflow tomorrow?", decision_registry, analytics_registry, decision_settings)
    assert not plan.analytics_calls and plan.requires_data_science
