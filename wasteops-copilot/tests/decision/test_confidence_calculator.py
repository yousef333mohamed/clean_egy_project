"""Evidence-quality confidence components and levels."""

from app.decision.confidence_calculator import ConfidenceCalculator
from app.decision.enums import ConfidenceLevel, DecisionEvidenceType


def test_complete_multi_source_evidence_is_high(decision_settings, evidence_factory):
    evidence = [
        evidence_factory(category="latest_bin_status"),
        evidence_factory(evidence_id="R1", source_type=DecisionEvidenceType.RULE, category="configured_rules", authority_level="configured"),
        evidence_factory(
            evidence_id="S1", source_type=DecisionEvidenceType.DOCUMENT, category="document_guidance", authority_level="official", recency="current"
        ),
    ]
    result = ConfidenceCalculator(decision_settings).calculate(evidence, ["latest_bin_status", "configured_rules"])
    assert result.level == ConfidenceLevel.HIGH and 0 <= result.score <= 1


def test_missing_and_null_evidence_reduce_confidence(decision_settings, evidence_factory):
    evidence = [evidence_factory(supporting_values={"has_data": False}, completeness_notes=["missing latest measurement"])]
    result = ConfidenceCalculator(decision_settings).calculate(evidence, ["latest_bin_status", "configured_rules"])
    assert result.components.retrieval_coverage == 0
    assert result.components.data_completeness == 0
    assert result.level == ConfidenceLevel.LOW


def test_synthetic_source_quality_penalty(decision_settings, evidence_factory):
    synthetic = evidence_factory(evidence_id="S1", source_type=DecisionEvidenceType.DOCUMENT, authority_level="demo_only", is_synthetic=True)
    result = ConfidenceCalculator(decision_settings).calculate([synthetic], ["latest_bin_status"])
    assert result.components.source_quality == 0.25


def test_disagreement_and_historical_period(decision_settings, evidence_factory):
    evidence = [evidence_factory(completeness_notes=["source conflict"]), evidence_factory(evidence_id="R1", source_type=DecisionEvidenceType.RULE)]
    result = ConfidenceCalculator(decision_settings).calculate(evidence, ["latest_bin_status"], explicitly_historical=True)
    assert result.components.source_agreement == 0.25
    assert result.components.recency == 0.9
