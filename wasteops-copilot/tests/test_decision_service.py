from app.schemas.retrieval import Evidence
from app.services.decision_service import calculate_confidence


def test_confidence_is_deterministic_and_evidence_based() -> None:
    evidence = [
        Evidence(content="fact", source_type="database", source_name="db", record_reference="1", relevance_score=1),
        Evidence(content="procedure", source_type="document", source_name="manual", record_reference="2", relevance_score=0.8),
    ]
    assert calculate_confidence(evidence, 0) == calculate_confidence(evidence, 0)
    assert calculate_confidence(evidence, 0) > calculate_confidence(evidence, 4)
    assert calculate_confidence([], 0) == 0
