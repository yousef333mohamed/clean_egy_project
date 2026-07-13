"""Document dry-run and idempotency service tests without external APIs."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.ingestion.document_ingestion_service import DocumentIngestionService
from app.models import DocumentStatus


class DryRunSession:
    async def rollback(self) -> None:
        return None


class ExplodingEmbeddings:
    async def embed_texts(self, _texts: list[str]) -> list[list[float]]:
        raise AssertionError("dry-run or duplicate ingestion must not call embeddings")


def settings(documents: Path) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        documents_directory=str(documents),
        data_dir=str(documents.parent),
        document_chunk_size=80,
        document_chunk_overlap=10,
        document_min_chunk_size=5,
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
