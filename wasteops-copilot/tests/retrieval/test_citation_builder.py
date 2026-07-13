"""Citation assignment and invalid-marker validation tests."""

from app.retrieval.citation_builder import CitationBuilder


def test_valid_duplicate_and_invalid_citations(evidence_factory) -> None:
    builder = CitationBuilder()
    citations = builder.assign([evidence_factory()])
    result = builder.validate_answer_citations("Inspect the sensor [S1] [S1]. Unknown [S9].", citations)
    assert result.valid_citation_ids == ["S1"]
    assert result.invalid_citation_ids == ["S9"]
    assert "[S9]" not in result.answer
    assert len(result.citations) == 1
    assert any("synthetic" in warning.lower() for warning in result.warnings)


def test_missing_citation_warning(evidence_factory) -> None:
    citations = CitationBuilder().assign([evidence_factory()])
    result = CitationBuilder().validate_answer_citations("A long procedural answer " * 10, citations)
    assert any("did not cite" in warning for warning in result.warnings)
