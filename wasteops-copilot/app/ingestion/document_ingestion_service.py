"""Version-safe knowledge-document extraction, embedding, and persistence."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.ingestion.document_chunker import DocumentChunker, PreparedChunk
from app.ingestion.document_discovery import MIME_TYPES, DocumentPathError, discover_documents, resolve_document
from app.ingestion.document_loader import load_document
from app.ingestion.document_metadata import load_document_metadata, merge_metadata
from app.ingestion.document_reports import write_document_failure_report
from app.ingestion.text_cleaner import clean_text, detect_language
from app.models import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.schemas.documents import DocumentIngestionResult, DocumentMetadata
from app.services.embedding_service import EmbeddingService
from app.utils.document_hash import hash_document
from app.utils.token_counter import TokenCounter

logger = get_logger(__name__)


class DocumentIngestionService:
    """Orchestrate deterministic document ingestion and safe version activation."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings | None = None,
        embedding_service: Any | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.embedding_service = embedding_service
        self.documents_dir = Path(self.settings.documents_directory)
        self.rejected_dir = Path(self.settings.data_dir) / "rejected"
        self.counter = TokenCounter(self.settings.embedding_model_name)
        self.chunker = DocumentChunker(
            self.counter,
            chunk_size=self.settings.document_chunk_size,
            overlap=self.settings.document_chunk_overlap,
            minimum=self.settings.document_min_chunk_size,
        )

    async def _successful_hash(self, file_hash: str) -> KnowledgeDocument | None:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.file_hash == file_hash,
            KnowledgeDocument.status.in_([DocumentStatus.COMPLETED, DocumentStatus.COMPLETED_WITH_WARNINGS, DocumentStatus.REPLACED]),
        )
        return (await self.session.scalars(statement)).first()

    async def _active_path(self, relative_path: str) -> KnowledgeDocument | None:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.original_path == relative_path,
            KnowledgeDocument.is_active.is_(True),
        )
        return (await self.session.scalars(statement)).first()

    async def _reusable_embeddings(self, chunks: list[PreparedChunk]) -> dict[str, list[float]]:
        hashes = list({chunk.content_hash for chunk in chunks})
        if not hashes:
            return {}
        statement = select(DocumentChunk.content_hash, DocumentChunk.embedding).where(
            DocumentChunk.content_hash.in_(hashes),
            DocumentChunk.embedding_model == self.settings.embedding_model_name,
            DocumentChunk.embedding_dimensions == self.settings.vector_dimensions,
        )
        rows = (await self.session.execute(statement)).all()
        return {content_hash: list(embedding) for content_hash, embedding in rows}

    @staticmethod
    def _result(
        *,
        document_id: str,
        source_filename: str,
        relative_path: str,
        status: DocumentStatus,
        dry_run: bool,
        file_size_bytes: int,
        started_at: datetime,
        pages: int = 0,
        characters: int = 0,
        tokens: int = 0,
        chunks: int = 0,
        embedded: int = 0,
        reused: int = 0,
        warnings: list[str] | None = None,
        failure_report: Path | None = None,
        error_message: str | None = None,
    ) -> DocumentIngestionResult:
        completed = datetime.now(UTC)
        return DocumentIngestionResult(
            document_id=document_id,
            source_filename=source_filename,
            relative_path=relative_path,
            status=status,
            dry_run=dry_run,
            file_size_bytes=file_size_bytes,
            pages_extracted=pages,
            characters_extracted=characters,
            tokens_extracted=tokens,
            chunks_created=chunks,
            chunks_embedded=embedded,
            embeddings_reused=reused,
            warnings=warnings or [],
            failure_report=str(failure_report) if failure_report else None,
            started_at=started_at,
            completed_at=completed,
            duration_seconds=max(0.0, (completed - started_at).total_seconds()),
            error_message=error_message,
        )

    async def ingest_document(
        self,
        relative_path: str,
        *,
        force: bool = False,
        dry_run: bool = False,
        metadata_override: DocumentMetadata | None = None,
    ) -> DocumentIngestionResult:
        """Validate and optionally embed one safely resolved relative document path."""
        discovered = resolve_document(self.documents_dir, relative_path, self.settings.document_max_file_size_mb)
        assert discovered.path is not None
        started = datetime.now(UTC)
        document_id = str(uuid.uuid4())
        file_hash = hash_document(discovered.path)
        existing = None if dry_run else await self._successful_hash(file_hash)
        if existing is not None and not force:
            return self._result(
                document_id=existing.document_id,
                source_filename=discovered.filename,
                relative_path=discovered.relative_path,
                status=DocumentStatus.SKIPPED_DUPLICATE,
                dry_run=False,
                file_size_bytes=discovered.size_bytes,
                started_at=started,
                pages=existing.total_pages,
                characters=existing.total_characters,
                tokens=existing.total_tokens,
                chunks=existing.total_chunks,
                reused=existing.total_chunks,
                warnings=["An identical document hash was already ingested; no embedding request was made."],
            )

        record: KnowledgeDocument | None = None
        warnings: list[str] = []
        stage = "metadata"
        pages = characters = tokens = chunk_count = embedded_count = reused_count = 0
        metadata = DocumentMetadata()
        try:
            metadata = merge_metadata(
                load_document_metadata(discovered.path, strict=self.settings.document_metadata_strict),
                metadata_override,
            )
            stage = "extraction"
            loaded = load_document(discovered.path)
            warnings.extend(loaded.warnings)
            cleaned_blocks = [
                type(block)(clean_text(block.text), block.page_number, block.section_title, block.kind) for block in loaded.blocks if clean_text(block.text)
            ]
            full_text = clean_text("\n\n".join(block.text for block in cleaned_blocks))
            if not full_text:
                raise ValueError("Document contains no usable text after cleaning")
            language = metadata.language or detect_language(full_text)
            pages = loaded.total_pages
            characters = len(full_text)
            tokens = self.counter.count(full_text)
            stage = "chunking"
            chunks = self.chunker.chunk(cleaned_blocks)
            if not chunks:
                raise ValueError("Document produced no valid chunks")
            chunk_count = len(chunks)
            if dry_run:
                status = DocumentStatus.COMPLETED_WITH_WARNINGS if warnings else DocumentStatus.COMPLETED
                return self._result(
                    document_id=document_id,
                    source_filename=discovered.filename,
                    relative_path=discovered.relative_path,
                    status=status,
                    dry_run=True,
                    file_size_bytes=discovered.size_bytes,
                    started_at=started,
                    pages=pages,
                    characters=characters,
                    tokens=tokens,
                    chunks=chunk_count,
                    warnings=warnings,
                )

            stage = "document_record"
            previous = await self._active_path(discovered.relative_path)
            record = KnowledgeDocument(
                document_id=document_id,
                source_filename=discovered.filename,
                original_path=discovered.relative_path,
                file_extension=discovered.extension,
                mime_type=MIME_TYPES[discovered.extension],
                document_type=metadata.document_type,
                department=metadata.department,
                asset_type=metadata.asset_type,
                region=metadata.region,
                effective_date=metadata.effective_date,
                version=metadata.version,
                language=language,
                is_synthetic=metadata.is_synthetic,
                authority_level=metadata.authority_level or "unknown",
                expiration_date=metadata.expiration_date,
                title=metadata.title or discovered.path.stem,
                file_hash=file_hash,
                file_size_bytes=discovered.size_bytes,
                status=DocumentStatus.PROCESSING,
                total_pages=pages,
                total_characters=characters,
                total_tokens=tokens,
                total_chunks=chunk_count,
                metadata_json={"source_metadata": loaded.source_metadata, "warnings": warnings},
                is_active=False,
            )
            self.session.add(record)
            await self.session.commit()

            stage = "embedding"
            reusable = await self._reusable_embeddings(chunks)
            await self.session.commit()
            missing_hashes = list(dict.fromkeys(chunk.content_hash for chunk in chunks if chunk.content_hash not in reusable))
            if missing_hashes:
                service = self.embedding_service or EmbeddingService(self.settings)
                content_by_hash = {chunk.content_hash: chunk.content for chunk in chunks}
                generated = await service.embed_texts([content_by_hash[content_hash] for content_hash in missing_hashes])
                reusable.update(dict(zip(missing_hashes, generated, strict=True)))
                embedded_count = len(missing_hashes)
            reused_count = chunk_count - embedded_count

            stage = "database_storage"
            embedded_at = datetime.now(UTC)
            common: dict[str, Any] = {
                "document_id": document_id,
                "source_filename": discovered.filename,
                "document_type": metadata.document_type,
                "department": metadata.department,
                "asset_type": metadata.asset_type,
                "region": metadata.region,
                "effective_date": metadata.effective_date,
                "version": metadata.version,
                "language": language,
                "embedding_model": self.settings.embedding_model_name,
                "embedding_dimensions": self.settings.vector_dimensions,
                "embedded_at": embedded_at,
            }
            self.session.add_all(
                [
                    DocumentChunk(
                        **common,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        chunk_number=chunk.chunk_number,
                        content=chunk.content,
                        content_hash=chunk.content_hash,
                        token_count=chunk.token_count,
                        embedding=reusable[chunk.content_hash],
                        metadata_json={"relative_path": discovered.relative_path},
                    )
                    for chunk in chunks
                ]
            )
            record.status = DocumentStatus.COMPLETED_WITH_WARNINGS if warnings else DocumentStatus.COMPLETED
            record.is_active = True
            if previous is not None and previous.document_id != document_id:
                previous.status = DocumentStatus.REPLACED
                previous.is_active = False
                previous.replaced_by_document_id = document_id
            await self.session.commit()
            return self._result(
                document_id=document_id,
                source_filename=discovered.filename,
                relative_path=discovered.relative_path,
                status=record.status,
                dry_run=False,
                file_size_bytes=discovered.size_bytes,
                started_at=started,
                pages=pages,
                characters=characters,
                tokens=tokens,
                chunks=chunk_count,
                embedded=embedded_count,
                reused=reused_count,
                warnings=warnings,
            )
        except Exception as exc:
            logger.exception(
                "document_ingestion_failed",
                source_filename=discovered.filename,
                relative_path=discovered.relative_path,
                stage=stage,
                error_type=type(exc).__name__,
            )
            await self.session.rollback()
            safe_message = str(exc) if isinstance(exc, (ValueError, DocumentPathError)) else f"{type(exc).__name__}: document ingestion failed"
            if not dry_run:
                if record is None:
                    record = KnowledgeDocument(
                        document_id=document_id,
                        source_filename=discovered.filename,
                        original_path=discovered.relative_path,
                        file_extension=discovered.extension,
                        mime_type=MIME_TYPES[discovered.extension],
                        language=metadata.language or "unknown",
                        is_synthetic=metadata.is_synthetic,
                        authority_level=metadata.authority_level or "unknown",
                        expiration_date=metadata.expiration_date,
                        title=metadata.title or discovered.path.stem,
                        file_hash=file_hash,
                        file_size_bytes=discovered.size_bytes,
                        status=DocumentStatus.FAILED,
                        total_pages=pages,
                        total_characters=characters,
                        total_tokens=tokens,
                        total_chunks=chunk_count,
                        error_message=safe_message,
                        metadata_json={"warnings": warnings, "failed_stage": stage},
                        is_active=False,
                    )
                    self.session.add(record)
                else:
                    record.status = DocumentStatus.FAILED
                    record.is_active = False
                    record.error_message = safe_message
                try:
                    await self.session.commit()
                except Exception:
                    logger.exception("document_failure_audit_write_failed", document_id=document_id)
                    await self.session.rollback()
            report = write_document_failure_report(
                self.rejected_dir,
                source_filename=discovered.filename,
                relative_path=discovered.relative_path,
                document_id=document_id,
                error_type=type(exc).__name__,
                error_message=safe_message,
                warnings=warnings,
                stage=stage,
            )
            return self._result(
                document_id=document_id,
                source_filename=discovered.filename,
                relative_path=discovered.relative_path,
                status=DocumentStatus.FAILED,
                dry_run=dry_run,
                file_size_bytes=discovered.size_bytes,
                started_at=started,
                pages=pages,
                characters=characters,
                tokens=tokens,
                chunks=chunk_count,
                embedded=embedded_count,
                reused=reused_count,
                warnings=warnings,
                failure_report=report,
                error_message=safe_message,
            )

    async def ingest_all_documents(self, *, force: bool = False, dry_run: bool = False) -> list[DocumentIngestionResult]:
        """Continue through every supported document even if one fails."""
        results: list[DocumentIngestionResult] = []
        for document in discover_documents(self.documents_dir, self.settings.document_max_file_size_mb):
            if document.supported:
                try:
                    results.append(await self.ingest_document(document.relative_path, force=force, dry_run=dry_run))
                except Exception as exc:
                    logger.exception(
                        "document_batch_item_failed",
                        source_filename=document.filename,
                        relative_path=document.relative_path,
                        error_type=type(exc).__name__,
                    )
                    document_id = str(uuid.uuid4())
                    report = write_document_failure_report(
                        self.rejected_dir,
                        source_filename=document.filename,
                        relative_path=document.relative_path,
                        document_id=document_id,
                        error_type=type(exc).__name__,
                        error_message="Document could not be started",
                        warnings=[],
                        stage="discovery",
                    )
                    results.append(
                        self._result(
                            document_id=document_id,
                            source_filename=document.filename,
                            relative_path=document.relative_path,
                            status=DocumentStatus.FAILED,
                            dry_run=dry_run,
                            file_size_bytes=document.size_bytes,
                            started_at=datetime.now(UTC),
                            failure_report=report,
                            error_message="Document could not be started",
                        )
                    )
        return results
