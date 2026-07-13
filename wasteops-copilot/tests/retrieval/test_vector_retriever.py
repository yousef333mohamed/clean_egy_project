"""Vector score conversion, ordering query, limits, and dimensions tests."""

from datetime import date
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.retrieval.vector_retriever import VectorRetriever
from app.schemas.retrieval import RetrievalFilters


def row(distance: float):
    mapping = {
        "chunk_id": 1,
        "document_id": "doc-1",
        "source_filename": "sensor.md",
        "document_title": "Sensor SOP",
        "document_type": "operational_sop",
        "department": None,
        "asset_type": "smart_bin",
        "region": None,
        "language": "en",
        "version": "1",
        "effective_date": date(2026, 1, 1),
        "expiration_date": None,
        "authority_level": "official",
        "page_number": None,
        "section_title": "Procedure",
        "chunk_number": 0,
        "content": "Sensor fault procedure",
        "content_hash": "hash",
        "is_synthetic": False,
        "raw_score": distance,
    }
    return SimpleNamespace(_mapping=mapping)


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
        vector_dimensions=3,
    )


@pytest.mark.asyncio
async def test_cosine_similarity_candidate_limit_and_filters() -> None:
    session = Session([row(0.2)])
    retriever = VectorRetriever(session, settings())
    result = await retriever.search([0.0, 0.0, 0.0], top_k=2, candidate_limit=5, filters=RetrievalFilters(asset_type="smart_bin"))
    assert result[0].vector_score == pytest.approx(0.8)
    assert session.statement._limit_clause.value == 5
    sql = str(session.statement)
    assert "knowledge_documents.is_active" in sql
    assert "knowledge_documents.status" in sql
    assert "lower(knowledge_documents.asset_type)" in sql


@pytest.mark.asyncio
async def test_embedding_dimension_validation() -> None:
    with pytest.raises(ValueError, match="3 dimensions"):
        await VectorRetriever(Session([]), settings()).search([0.0, 0.0], top_k=1)
