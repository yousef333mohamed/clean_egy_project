"""Decision orchestration, insufficiency, approval, citations, and failures."""

from datetime import UTC, datetime

import pytest

from app.decision.confidence_calculator import ConfidenceCalculator
from app.decision.decision_registry import build_decision_registry
from app.decision.enums import DecisionEvidenceType, DecisionType
from app.decision.evidence_collector import CollectedDecisionEvidence
from app.decision.option_generator import OptionGenerator
from app.decision.option_scorer import OptionScorer
from app.decision.risk_analyzer import RiskAnalyzer
from app.schemas.decision import DecisionRequest
from app.schemas.decision_context import DecisionContextPlan, DecisionRouteResult
from app.schemas.decision_evidence import DecisionEvidence
from app.schemas.operational_evidence import DataPeriod, OperationalEvidence
from app.services.decision_intelligence_service import DecisionIntelligenceService


class Router:
    def __init__(self, route):
        self.result = route

    async def route(self, _request):
        return self.result


class Planner:
    def __init__(self, plan):
        self.result = plan

    def plan(self, _request, _route):
        return self.result


class Collector:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    async def collect(self, _request, _plan):
        if self.error:
            raise self.error
        return self.result


class LLM:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error

    async def generate_grounded_answer(self, **_kwargs):
        if self.error:
            raise self.error
        return self.answer


def route(decision_type=DecisionType.BIN_ATTENTION_PRIORITY, **updates):
    return DecisionRouteResult(decision_type=decision_type, required_analytics_tools=[], **updates)


def plan(decision_type=DecisionType.BIN_ATTENTION_PRIORITY):
    return DecisionContextPlan(
        decision_type=decision_type, analytics_calls=[], document_queries=[], required_evidence_categories=["latest_bin_status", "configured_rules"]
    )


def collected(has_data=True):
    database = OperationalEvidence(
        evidence_id="D1",
        tool_name="list_critical_bins",
        description="Critical bins",
        filters={},
        columns=["bin_id"],
        rows=[{"bin_id": "BIN-1"}] if has_data else [],
        record_count=1 if has_data else 0,
        data_period=DataPeriod(start="2026-03-01", end="2026-03-31"),
        generated_at=datetime.now(UTC),
    )
    return CollectedDecisionEvidence(
        evidence=[
            DecisionEvidence(
                evidence_id="D1",
                source_type=DecisionEvidenceType.DATABASE,
                category="latest_bin_status",
                description="Critical bins",
                authority_level="database",
                recency="latest_available",
                supporting_values={"has_data": has_data, "result_row_count": 3 if has_data else 0},
            ),
            DecisionEvidence(
                evidence_id="R1",
                source_type=DecisionEvidenceType.RULE,
                category="configured_rules",
                description="80% threshold",
                authority_level="configured",
                recency="current_configuration",
                supporting_values={"threshold_pct": 80},
            ),
        ],
        database_evidence=[database],
        warnings=["The 80% threshold is configured rather than official."],
    )


def service(settings, collector, selected_route=None, selected_plan=None, llm=None):
    registry = build_decision_registry()
    return DecisionIntelligenceService(
        Router(selected_route or route()),
        Planner(selected_plan or plan()),
        collector,
        OptionGenerator(registry, settings),
        OptionScorer(settings),
        ConfidenceCalculator(settings),
        RiskAnalyzer(),
        registry,
        settings,
        llm_service=llm,
    )


async def test_successful_recommendation_has_alternatives_and_approval(decision_settings):
    response = await service(decision_settings, Collector(collected())).recommend(DecisionRequest(question="Which bins need attention?"))
    assert response.recommended_option is not None and response.alternative_options
    assert response.requires_human_approval is True and response.grounded
    assert any("authorized operations manager" in warning for warning in response.warnings)


async def test_response_cannot_disable_human_approval(decision_settings):
    unsafe_development_setting = decision_settings.model_copy(update={"decision_require_human_approval": False})
    response = await service(unsafe_development_setting, Collector(collected())).recommend(DecisionRequest(question="Which bins need attention?"))
    assert response.requires_human_approval is True


async def test_no_data_forces_insufficient_context(decision_settings):
    response = await service(decision_settings, Collector(collected(False))).recommend(DecisionRequest(question="Which bins need attention?"))
    assert response.recommended_option is None and response.insufficient_context


@pytest.mark.parametrize(
    ("decision_type", "kwargs"),
    [
        (DecisionType.UNSUPPORTED_PREDICTIVE_DECISION, {"requires_data_science": True, "unsupported_reason": "prediction required"}),
        (DecisionType.UNSUPPORTED_OPTIMIZATION, {"requires_optimization": True, "unsupported_reason": "optimization required"}),
        (DecisionType.UNSUPPORTED_AUTONOMOUS_ACTION, {"unsupported_reason": "execution prohibited"}),
    ],
)
async def test_unsupported_requests_return_200_style_response_without_collection(decision_settings, decision_type, kwargs):
    selected = route(decision_type, **kwargs)
    response = await service(
        decision_settings,
        Collector(error=AssertionError("must not collect")),
        selected_route=selected,
        selected_plan=DecisionContextPlan(
            decision_type=decision_type,
            analytics_calls=[],
            document_queries=[],
            required_evidence_categories=[],
            **{k: v for k, v in kwargs.items() if k in {"requires_data_science", "requires_optimization", "unsupported_reason"}},
        ),
    ).recommend(DecisionRequest(question="unsupported"))
    assert response.recommended_option is None and response.requires_human_approval


async def test_invalid_generated_citation_removed(decision_settings):
    response = await service(decision_settings, Collector(collected()), llm=LLM("Recommendation [D1] [M9]")).recommend(
        DecisionRequest(question="Which bins need attention?")
    )
    assert "[M9]" not in response.situation_summary
    assert any("Invalid generated" in warning for warning in response.warnings)


async def test_generated_execution_language_is_replaced(decision_settings):
    response = await service(decision_settings, Collector(collected()), llm=LLM("Review critical-fill bins. Dispatch the truck [D1]")).recommend(
        DecisionRequest(question="Which bins need attention?")
    )
    assert "Dispatch" not in response.situation_summary
    assert any("execution language" in warning for warning in response.warnings)


async def test_arabic_fallback_answer(decision_settings):
    response = await service(decision_settings, Collector(collected())).recommend(DecisionRequest(question="ما أفضل إجراء للحاويات؟"))
    assert "الإجراء الموصى به" in response.situation_summary


async def test_provider_and_database_failures_propagate(decision_settings):
    with pytest.raises(RuntimeError):
        await service(decision_settings, Collector(error=RuntimeError("database offline"))).recommend(DecisionRequest(question="bins"))
    with pytest.raises(RuntimeError):
        await service(decision_settings, Collector(collected()), llm=LLM(error=RuntimeError("model offline"))).recommend(DecisionRequest(question="bins"))
