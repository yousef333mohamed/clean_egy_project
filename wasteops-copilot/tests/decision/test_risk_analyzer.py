"""Situation-specific qualitative decision risks."""

from app.decision.enums import ActionCategory, DecisionEvidenceType, RiskCategory
from app.decision.risk_analyzer import RiskAnalyzer
from app.schemas.decision_option import CandidateDecisionOption


def option(category):
    return CandidateDecisionOption(
        option_id="O1", action_category=category, title="x", action="x", supporting_evidence_ids=["D1"], operational_requirements=["Manager confirmation"]
    )


def test_resource_and_continuity_risks(evidence_factory):
    risks = RiskAnalyzer().analyze(option(ActionCategory.PRIORITIZE_COLLECTION_REVIEW), [evidence_factory(description="Critical bins")])
    categories = {item.category for item in risks}
    assert RiskCategory.RESOURCE in categories and RiskCategory.SERVICE_CONTINUITY in categories


def test_data_quality_and_policy_authority_risks(evidence_factory):
    evidence = [
        evidence_factory(completeness_notes=["missing fill level"]),
        evidence_factory(evidence_id="S1", source_type=DecisionEvidenceType.DOCUMENT, authority_level="unknown", is_synthetic=True),
    ]
    categories = {item.category for item in RiskAnalyzer().analyze(option(ActionCategory.REQUEST_INSPECTION), evidence)}
    assert RiskCategory.DATA_QUALITY in categories and RiskCategory.POLICY_AUTHORITY in categories


def test_no_action_risk_only_when_condition_is_urgent(evidence_factory):
    risks = RiskAnalyzer().analyze(option(ActionCategory.CONTINUE_MONITORING), [evidence_factory(description="Current sensor fault")])
    assert RiskCategory.NO_ACTION in {item.category for item in risks}
    assert all(item.likelihood == "POSSIBLE" for item in risks)


def test_safety_risk_requires_safety_evidence(evidence_factory):
    evidence = [evidence_factory(description="Official safety inspection condition")]
    categories = {item.category for item in RiskAnalyzer().analyze(option(ActionCategory.REQUEST_INSPECTION), evidence)}
    assert RiskCategory.SAFETY in categories
