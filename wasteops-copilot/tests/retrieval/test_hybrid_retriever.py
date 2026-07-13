"""Hybrid score fusion and deterministic deduplication tests."""

import pytest

from app.core.config import Settings
from app.retrieval.hybrid_retriever import HybridRetriever


def settings(**overrides):
    values = {
        "database_url": "postgresql+asyncpg://test:test@database/test",
        "database_sync_url": "postgresql+psycopg://test:test@database/test",
        "vector_dimensions": 3,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.asyncio
async def test_weighted_merge_identifier_boost_and_vector_only(evidence_factory) -> None:
    vector_item = evidence_factory(vector_score=0.8, keyword_score=0, final_score=0.8)
    keyword_item = evidence_factory(vector_score=0, keyword_score=0.6, final_score=0.6)

    class Vector:
        async def search(self, *_args, **_kwargs):
            return [vector_item]

    class Keyword:
        async def search(self, *_args, **_kwargs):
            return [keyword_item]

    hybrid = HybridRetriever(Vector(), Keyword(), settings())
    result = await hybrid.search("BIN-DEMO-001", [0.0] * 3, top_k=8)
    assert len(result) == 1
    assert result[0].vector_score == 0.8
    assert result[0].keyword_score == 0.6
    assert result[0].final_score == pytest.approx(0.85)

    vector_only = HybridRetriever(Vector(), Keyword(), settings(retrieval_enable_hybrid=False))
    assert (await vector_only.search("sensor", [0.0] * 3, top_k=8))[0].final_score == 0.8
