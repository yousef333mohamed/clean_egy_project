"""Multilingual deterministic query-processing tests."""

import pytest

from app.core.config import Settings
from app.retrieval.query_processor import QueryProcessingError, QueryProcessor


def settings(**overrides):
    values = {
        "database_url": "postgresql+asyncpg://test:test@database/test",
        "database_sync_url": "postgresql+psycopg://test:test@database/test",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.asyncio
async def test_empty_english_arabic_and_mixed_queries() -> None:
    processor = QueryProcessor(settings(retrieval_enable_query_rewrite=False))
    with pytest.raises(QueryProcessingError):
        await processor.process("   ")
    assert (await processor.process("sensor failure procedure")).language == "en"
    assert (await processor.process("إجراء توقف حساس الحاوية")).language == "ar"
    assert (await processor.process("sensor توقف الحساس")).language == "mixed"


@pytest.mark.asyncio
async def test_identifiers_dates_and_original_query_are_preserved() -> None:
    query = "  Check   BIN-DEMO-001 on 2026-01-01 for TRK-DEMO-01  "
    result = await QueryProcessor(settings(retrieval_enable_query_rewrite=False)).process(query)
    assert result.original_query == query
    assert result.normalized_query == "Check BIN-DEMO-001 on 2026-01-01 for TRK-DEMO-01"
    assert result.entities.bin_ids == ["BIN-DEMO-001"]
    assert result.entities.truck_ids == ["TRK-DEMO-01"]
    assert result.entities.dates == ["2026-01-01"]


@pytest.mark.asyncio
async def test_rewrite_validation_and_fallback() -> None:
    class Rewriter:
        async def rewrite_query(self, _query):
            return {"rewritten_query": "sensor fault SOP", "keywords": ["sensor"], "document_types": [], "asset_types": []}

    result = await QueryProcessor(settings(), rewriter=Rewriter()).process("sensor fault")
    assert result.rewritten_query == "sensor fault SOP"

    class Invalid:
        async def rewrite_query(self, _query):
            return {"rewritten_query": "changed", "keywords": []}

    fallback = await QueryProcessor(settings(), rewriter=Invalid()).process("BIN-DEMO-001?")
    assert fallback.rewritten_query is None
