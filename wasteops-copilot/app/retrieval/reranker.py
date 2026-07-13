"""Explainable deterministic evidence reranking."""

from datetime import UTC, datetime

from app.schemas.retrieval import RetrievedEvidence
from app.utils.text_similarity import exact_identifier_match, term_coverage, terms


class EvidenceReranker:
    """Blend 75% retrieval score with 25% deterministic relevance features.

    Feature score: 65% query-term coverage, 20% identifier match, 10% section
    title coverage, and 5% effective-date freshness. This is a ranking score,
    not a calibrated probability.
    """

    async def rerank(self, query: str, evidence: list[RetrievedEvidence], *, top_k: int) -> list[RetrievedEvidence]:
        current_year = datetime.now(UTC).year
        ranked = []
        for item in evidence:
            content = item.content or item.content_preview
            coverage = term_coverage(query, content)
            identifier = 1.0 if exact_identifier_match(query, content) else 0.0
            section = term_coverage(query, item.section_title or "")
            if item.effective_date is None:
                freshness = 0.25
            else:
                age = max(0, current_year - item.effective_date.year)
                freshness = max(0.0, 1.0 - age / 10)
            heuristic = min(1.0, 0.65 * coverage + 0.20 * identifier + 0.10 * section + 0.05 * freshness)
            updated = item.model_copy(deep=True)
            updated.rerank_score = heuristic
            updated.final_score = min(1.0, 0.75 * item.final_score + 0.25 * heuristic)
            ranked.append(updated)
        return sorted(ranked, key=lambda item: (-item.final_score, -len(terms(item.section_title or "")), item.chunk_id))[:top_k]
