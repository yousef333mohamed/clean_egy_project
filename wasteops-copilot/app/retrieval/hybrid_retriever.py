"""Weighted vector/keyword candidate fusion."""

from app.core.config import Settings, get_settings
from app.schemas.retrieval import RetrievalFilters, RetrievedEvidence
from app.utils.text_similarity import exact_identifier_match


class HybridRetriever:
    """Merge candidates by chunk ID using configured weighted scores."""

    def __init__(self, vector_retriever, keyword_retriever, settings: Settings | None = None) -> None:
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.settings = settings or get_settings()
        self.last_vector_count = 0
        self.last_keyword_count = 0

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        *,
        top_k: int,
        filters: RetrievalFilters | None = None,
        candidate_limit: int | None = None,
    ) -> list[RetrievedEvidence]:
        vector = await self.vector_retriever.search(query_embedding, top_k=top_k, filters=filters, candidate_limit=candidate_limit)
        self.last_vector_count = len(vector)
        if not self.settings.retrieval_enable_hybrid:
            self.last_keyword_count = 0
            return vector
        keyword = await self.keyword_retriever.search(query, top_k=top_k, filters=filters, candidate_limit=candidate_limit)
        self.last_keyword_count = len(keyword)
        merged: dict[str, RetrievedEvidence] = {item.chunk_id: item.model_copy(deep=True) for item in vector}
        for item in keyword:
            if item.chunk_id in merged:
                merged[item.chunk_id].keyword_score = item.keyword_score
            else:
                merged[item.chunk_id] = item.model_copy(deep=True)
        for item in merged.values():
            score = item.vector_score * self.settings.retrieval_vector_weight + item.keyword_score * self.settings.retrieval_keyword_weight
            if item.content and exact_identifier_match(query, item.content):
                score += 0.1
            item.final_score = min(1.0, score)
        return sorted(merged.values(), key=lambda item: (-item.final_score, item.chunk_id))
