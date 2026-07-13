"""Document dry-run and idempotency service tests without external APIs."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.ingestion.document_ingestion_service import DocumentIngestionService
from app.models import DocumentStatus


class DryRunSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_all(self, values: list[object]) -> None:
        self.added.extend(values)

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class ExplodingEmbeddings:
    async def embed_texts(self, _texts: list[str]) -> list[list[float]]:
        raise AssertionError("dry-run or duplicate ingestion must not call embeddings")


class FakeEmbeddings:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 0.0, 0.0] for _ in texts]


def settings(documents: Path) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        documents_directory=str(documents),
        data_dir=str(documents.parent),
        document_chunk_size=80,
        document_chunk_overlap=10,
        document_min_chunk_size=5,
        vector_dimensions=3,
    )


@pytest.mark.asyncio
async def test_dry_run_extracts_and_chunks_without_embedding(tmp_path: Path) -> None:
    path = tmp_path / "manual.md"
    path.write_text("# Purpose\n\nInspect BIN-01 before collection.\n\n## Procedure\n\nRecord every result.", encoding="utf-8")
    service = DocumentIngestionService(DryRunSession(), settings=settings(tmp_path), embedding_service=ExplodingEmbeddings())
    result = await service.ingest_document("manual.md", dry_run=True)
    assert result.status == DocumentStatus.COMPLETED
    assert result.tokens_extracted > 0
    assert result.chunks_created > 0
    assert result.chunks_embedded == 0


@pytest.mark.asyncio
async def test_duplicate_hash_skips_embedding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "manual.md"
    path.write_text("# Demo\n\nContent", encoding="utf-8")
    service = DocumentIngestionService(DryRunSession(), settings=settings(tmp_path), embedding_service=ExplodingEmbeddings())
    existing = SimpleNamespace(
        document_id="existing-id",
        total_pages=0,
        total_characters=12,
        total_tokens=3,
        total_chunks=1,
    )

    async def successful(_hash: str) -> SimpleNamespace:
        return existing

    monkeypatch.setattr(service, "_successful_hash", successful)
    result = await service.ingest_document("manual.md")
    assert result.status == DocumentStatus.SKIPPED_DUPLICATE
    assert result.document_id == "existing-id"
    assert result.embeddings_reused == 1


@pytest.mark.asyncio
async def test_changed_path_activates_new_version_only_after_chunks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "manual.md"
    path.write_text("# Procedure\n\nInspect TRK-01 and record the result before departure.", encoding="utf-8")
    session = DryRunSession()
    service = DocumentIngestionService(session, settings=settings(tmp_path), embedding_service=FakeEmbeddings())
    previous = SimpleNamespace(document_id="old-id", status=DocumentStatus.COMPLETED, is_active=True, replaced_by_document_id=None)

    async def no_hash(_hash: str) -> None:
        return None

    async def active(_path: str) -> SimpleNamespace:
        return previous

    async def no_reuse(_chunks: list[object]) -> dict[str, list[float]]:
        return {}

    monkeypatch.setattr(service, "_successful_hash", no_hash)
    monkeypatch.setattr(service, "_active_path", active)
    monkeypatch.setattr(service, "_reusable_embeddings", no_reuse)
    result = await service.ingest_document("manual.md")
    assert result.status == DocumentStatus.COMPLETED
    assert result.chunks_embedded == result.chunks_created
    assert previous.status == DocumentStatus.REPLACED
    assert previous.is_active is False
    assert previous.replaced_by_document_id == result.document_id
    stored_chunks = [item for item in session.added if item.__class__.__name__ == "DocumentChunk"]
    assert stored_chunks
    assert all(chunk.embedding_dimensions == 3 for chunk in stored_chunks)
