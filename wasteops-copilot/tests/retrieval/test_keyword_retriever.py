"""Keyword exact-ID, Arabic fallback, stop words, and normalization tests."""

from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.retrieval.keyword_retriever import KeywordRetriever, keyword_tokens
from tests.retrieval.test_vector_retriever import row


class Session:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return SimpleNamespace(all=lambda: self.rows)


def settings():
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
    )


@pytest.mark.asyncio
async def test_exact_identifier_and_score_normalization() -> None:
    item = row(0.5)
    item._mapping["content"] = "Inspect BIN-DEMO-001 sensor fault"
    session = Session([item])
    results = await KeywordRetriever(session, settings()).search("BIN-DEMO-001 sensor", top_k=2)
    assert 0 <= results[0].keyword_score <= 1
    assert results[0].keyword_score > 0.5
    assert "LIKE" in str(session.statement)


@pytest.mark.asyncio
async def test_arabic_tokens_and_stop_word_only_query() -> None:
    assert "الحساس" in keyword_tokens("توقف الحساس عن الإرسال")
    assert await KeywordRetriever(Session([]), settings()).search("the and is", top_k=2) == []
