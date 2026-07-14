"""End-to-end query processing, candidate retrieval, reranking, and diversity."""

import time
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.retrieval.metadata_filters import normalized_filters
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.utils.text_similarity import limit_document_chunks
from app.observability.tracer import Tracer
from app.observability.context import request_id_var
from app.core.database import AsyncSessionLocal

logger = get_logger(__name__)


class RetrievalService:
    """Coordinate injected query, embedding, hybrid, and reranking services."""

    def __init__(self, query_processor, embedding_service, hybrid_retriever, reranker, settings: Settings | None = None, tracer: Tracer | None = None) -> None:
        self.query_processor = query_processor
        self.embedding_service = embedding_service
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.settings = settings or get_settings()
        self.tracer = tracer or Tracer(session_factory=AsyncSessionLocal, settings=self.settings)

    async def search(self, request: RetrievalRequest, *, request_id: str | None = None) -> RetrievalResponse:
        token = request_id_var.set(request_id) if request_id else None
        try:
            async with self.tracer.span("RETRIEVAL", {"filters": normalized_filters(request.filters), "top_k": request.top_k}) as span:
                response = await self._search(request, request_id=request_id)
                span.set_metric("retrieved_chunks", len(response.evidence))
                span.set_metric("insufficient_context", not response.evidence)
                return response
        finally:
            if token is not None:
                request_id_var.reset(token)

    async def _search(self, request: RetrievalRequest, *, request_id: str | None = None) -> RetrievalResponse:
        started = time.perf_counter()
        processed = await self.query_processor.process(request.query)
        embedding = await self.embedding_service.embed_text(processed.retrieval_query)
        candidate_limit = max(request.top_k, self.settings.retrieval_candidate_limit)
        candidates = await self.hybrid_retriever.search(
            processed.retrieval_query,
            embedding,
            top_k=request.top_k,
            filters=request.filters,
            candidate_limit=candidate_limit,
        )
        if self.settings.retrieval_enable_reranking:
            candidates = await self.reranker.rerank(
                processed.retrieval_query,
                candidates,
                top_k=candidate_limit,
            )
        above_threshold = [item for item in candidates if item.final_score >= self.settings.retrieval_min_score]
        diverse = limit_document_chunks(above_threshold, self.settings.retrieval_max_chunks_per_document)[: request.top_k]
        warnings = []
        if processed.language in {"ar", "mixed"}:
            warnings.append("Arabic retrieval uses hybrid token matching without claiming Arabic linguistic stemming.")
        duration = time.perf_counter() - started
        debug: dict[str, Any] | None = None
        if request.debug:
            debug = {
                "vector_candidates": self.hybrid_retriever.last_vector_count,
                "keyword_candidates": self.hybrid_retriever.last_keyword_count,
                "merged_candidates": len(candidates),
                "threshold": self.settings.retrieval_min_score,
                "candidate_limit": candidate_limit,
                "duration_seconds": duration,
            }
        logger.info(
            "retrieval_completed",
            request_id=request_id,
            query_language=processed.language,
            rewritten=processed.rewritten_query is not None,
            vector_candidates=self.hybrid_retriever.last_vector_count,
            keyword_candidates=self.hybrid_retriever.last_keyword_count,
            final_chunks=len(diverse),
            filters=normalized_filters(request.filters),
            duration_seconds=duration,
            insufficient_context=not diverse,
        )
        return RetrievalResponse(
            query=processed.normalized_query,
            rewritten_query=processed.rewritten_query,
            language=processed.language,
            evidence=diverse,
            filters_applied=normalized_filters(request.filters),
            warnings=warnings,
            debug=debug,
        )
