"""Threshold, diversity, filters, and Arabic warning orchestration tests."""

import pytest

from app.core.config import Settings
from app.retrieval.retrieval_service import RetrievalService
from app.schemas.retrieval import ProcessedQuery, QueryEntities, RetrievalFilters, RetrievalRequest


def settings():
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        vector_dimensions=3,
        retrieval_min_score=0.45,
        retrieval_max_chunks_per_document=1,
    )


class Processor:
    async def process(self, query):
        return ProcessedQuery(
            original_query=query,
            normalized_query=query.strip(),
            language="ar" if "حساس" in query else "en",
            entities=QueryEntities(),
        )


class Embeddings:
    async def embed_text(self, _text):
        return [0.0, 0.0, 0.0]


@pytest.mark.asyncio
async def test_threshold_document_limit_and_filters(evidence_factory) -> None:
    items = [
        evidence_factory(chunk_id="1", final_score=0.8, content_hash="1"),
        evidence_factory(chunk_id="2", final_score=0.7, content_hash="2"),
        evidence_factory(chunk_id="3", document_id="doc-2", final_score=0.2, content_hash="3"),
    ]

    class Hybrid:
        last_vector_count = 3
        last_keyword_count = 2

        async def search(self, *_args, **_kwargs):
            return items

    class Reranker:
        async def rerank(self, _query, evidence, *, top_k):
            return evidence[:top_k]

    service = RetrievalService(Processor(), Embeddings(), Hybrid(), Reranker(), settings())
    response = await service.search(RetrievalRequest(query="sensor", filters=RetrievalFilters(asset_type="smart_bin"), debug=True))
    assert [item.chunk_id for item in response.evidence] == ["1"]
    assert response.filters_applied == {"asset_type": ["smart_bin"]}
    assert response.debug["threshold"] == 0.45

    arabic = await service.search(RetrievalRequest(query="توقف حساس الحاوية"))
    assert any("Arabic" in warning for warning in arabic.warnings)
