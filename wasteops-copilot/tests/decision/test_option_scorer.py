"""Deterministic weighted option scoring."""

from app.decision.enums import DecisionEvidenceType, DecisionType
from app.decision.option_generator import OptionGenerator
from app.decision.option_scorer import OptionScorer
from app.schemas.decision import DecisionRequest


def options(registry, settings, evidence):
    request = DecisionRequest(question="Which bins need attention?")
    return request, OptionGenerator(registry, settings).generate(request, DecisionType.BIN_ATTENTION_PRIORITY, evidence)


def test_scores_are_bounded_and_deterministic(decision_registry, decision_settings, evidence_factory):
    evidence = [evidence_factory(description="Critical bins", supporting_values={"has_data": True, "result_row_count": 12})]
    request, candidates = options(decision_registry, decision_settings, evidence)
    first = OptionScorer(decision_settings).score(candidates, evidence, request.constraints)
    second = OptionScorer(decision_settings).score(candidates, evidence, request.constraints)
    assert first == second
    assert all(0 <= item.score <= 1 for item in first)
    assert first[0].score_breakdown.service_impact >= 0.8
    assert first[0].score_breakdown.urgency >= 0.7


def test_synthetic_document_policy_penalty(decision_registry, decision_settings, evidence_factory):
    database = evidence_factory()
    synthetic = evidence_factory(
        evidence_id="S1",
        source_type=DecisionEvidenceType.DOCUMENT,
        category="document_guidance",
        authority_level="demo_only",
        recency="current",
        is_synthetic=True,
    )
    request, candidates = options(decision_registry, decision_settings, [database, synthetic])
    scored = OptionScorer(decision_settings).score(candidates, [database, synthetic], request.constraints)
    assert all(item.score_breakdown.policy_alignment == 0.25 for item in scored)


def test_no_document_is_neutral_by_default(decision_registry, decision_settings, evidence_factory):
    evidence = [evidence_factory()]
    request, candidates = options(decision_registry, decision_settings, evidence)
    scored = OptionScorer(decision_settings).score(candidates, evidence, request.constraints)
    assert scored[0].score_breakdown.policy_alignment == 0.5


def test_weighted_formula_matches_breakdown(decision_registry, decision_settings, evidence_factory):
    evidence = [evidence_factory()]
    request, candidates = options(decision_registry, decision_settings, evidence)
    item = OptionScorer(decision_settings).score(candidates, evidence, request.constraints)[0]
    b = item.score_breakdown
    expected = b.service_impact * 0.3 + b.urgency * 0.25 + b.risk_control * 0.2 + b.feasibility * 0.15 + b.policy_alignment * 0.1
    assert item.score == round(expected, 6)
