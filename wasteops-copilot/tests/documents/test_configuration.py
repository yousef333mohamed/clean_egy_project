"""Document configuration validation and migration index tests."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def base_settings(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://test:test@database/test",
        "database_sync_url": "postgresql+psycopg://test:test@database/test",
    }
    values.update(overrides)
    return values


def test_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValidationError, match="OVERLAP"):
        Settings(**base_settings(document_chunk_size=100, document_chunk_overlap=100))


def test_retrieval_candidate_limit_and_weights_are_validated() -> None:
    with pytest.raises(ValidationError, match="CANDIDATE_LIMIT"):
        Settings(**base_settings(retrieval_top_k=10, retrieval_candidate_limit=5))
    with pytest.raises(ValidationError, match="must add up"):
        Settings(**base_settings(retrieval_vector_weight=0.8, retrieval_keyword_weight=0.3))


def test_embedding_environment_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL", "compatible-model")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "7")
    settings = Settings(**base_settings())
    assert settings.embedding_model_name == "compatible-model"
    assert settings.vector_dimensions == 7


def test_migration_uses_hnsw_cosine_index() -> None:
    migration = Path("migrations/versions/0003_document_ingestion.py").read_text(encoding="utf-8")
    assert 'postgresql_using="hnsw"' in migration
    assert '"vector_cosine_ops"' in migration
