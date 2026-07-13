"""Stable evidence citation assignment and answer-marker validation."""

import re

from app.schemas.citation import Citation, CitationValidationResult
from app.schemas.retrieval import RetrievedEvidence


class CitationBuilder:
    """Map only supplied evidence to source labels; never fabricate sources."""

    def assign(self, evidence: list[RetrievedEvidence]) -> list[Citation]:
        return [
            Citation(
                citation_id=f"S{index}",
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                source_filename=item.source_filename,
                document_title=item.document_title,
                page_number=item.page_number,
                section_title=item.section_title,
                chunk_number=item.chunk_number,
                content_preview=item.content_preview,
                is_synthetic=item.is_synthetic,
            )
            for index, item in enumerate(evidence, start=1)
        ]

    def validate_answer_citations(self, answer: str, citations: list[Citation]) -> CitationValidationResult:
        available = {citation.citation_id: citation for citation in citations}
        markers = re.findall(r"\[(S\d+)\]", answer)
        invalid = list(dict.fromkeys(marker for marker in markers if marker not in available))
        cleaned = answer
        for marker in invalid:
            cleaned = re.sub(rf"\s*\[{re.escape(marker)}\]", "", cleaned)
        valid = list(dict.fromkeys(marker for marker in markers if marker in available))
        warnings = []
        if invalid:
            warnings.append(f"Removed invalid citation markers: {', '.join(invalid)}.")
        if len(cleaned) > 80 and not valid:
            warnings.append("The generated answer did not cite supplied evidence.")
        selected = [available[marker] for marker in valid]
        if any(citation.is_synthetic for citation in selected):
            warnings.append("The cited evidence includes synthetic demo material that is not official policy.")
        return CitationValidationResult(
            answer=cleaned,
            citations=selected,
            valid_citation_ids=valid,
            invalid_citation_ids=invalid,
            warnings=warnings,
        )
