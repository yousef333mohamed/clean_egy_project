"""Safe document discovery, ingestion, history, and chunk APIs."""

from typing import Annotated
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.ingestion.document_discovery import DocumentPathError, discover_documents
from app.ingestion.document_ingestion_service import DocumentIngestionService
from app.models import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.schemas.documents import (
    DiscoveredDocumentResponse,
    DocumentChunkPage,
    DocumentChunkResponse,
    DocumentIngestAllRequest,
    DocumentIngestRequest,
    DocumentIngestionResult,
    DocumentPathRequest,
    KnowledgeDocumentPage,
    KnowledgeDocumentResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])
AppSettings = Annotated[Settings, Depends(get_settings)]


def _require_enabled(settings: Settings) -> None:
    if not settings.enable_document_ingestion_api:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document ingestion API is disabled")


def _path_error(exc: DocumentPathError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(status_code=code, detail=str(exc))


@router.get("/files", response_model=list[DiscoveredDocumentResponse])
async def list_document_files(settings: AppSettings) -> list[DiscoveredDocumentResponse]:
    """Return safe metadata for supported and rejected discovered files."""
    return [
        DiscoveredDocumentResponse(
            filename=item.filename,
            relative_path=item.relative_path,
            extension=item.extension,
            size_bytes=item.size_bytes,
            modified_at=item.modified_at,
            supported=item.supported,
            rejection_reason=item.rejection_reason,
        )
        for item in discover_documents(Path(settings.documents_directory), settings.document_max_file_size_mb)
    ]


@router.post("/validate", response_model=DocumentIngestionResult)
async def validate_document(request: DocumentPathRequest, session: DatabaseSession, settings: AppSettings) -> DocumentIngestionResult:
    """Extract and chunk one document without requesting embeddings."""
    _require_enabled(settings)
    try:
        return await DocumentIngestionService(session, settings=settings).ingest_document(request.relative_path, dry_run=True)
    except DocumentPathError as exc:
        raise _path_error(exc) from exc


@router.post("/ingest", response_model=DocumentIngestionResult)
async def ingest_document(request: DocumentIngestRequest, session: DatabaseSession, settings: AppSettings) -> DocumentIngestionResult:
    """Embed and store one safely resolved document."""
    _require_enabled(settings)
    try:
        return await DocumentIngestionService(session, settings=settings).ingest_document(
            request.relative_path,
            force=request.force,
            metadata_override=request.metadata,
        )
    except DocumentPathError as exc:
        raise _path_error(exc) from exc


@router.post("/ingest-all", response_model=list[DocumentIngestionResult])
async def ingest_all_documents(
    request: DocumentIngestAllRequest,
    session: DatabaseSession,
    settings: AppSettings,
) -> list[DocumentIngestionResult]:
    """Process all supported documents, continuing after per-document failures."""
    _require_enabled(settings)
    return await DocumentIngestionService(session, settings=settings).ingest_all_documents(force=request.force, dry_run=request.dry_run)


@router.get("", response_model=KnowledgeDocumentPage)
async def list_knowledge_documents(
    session: DatabaseSession,
    document_type: str | None = None,
    department: str | None = None,
    asset_type: str | None = None,
    region: str | None = None,
    language: str | None = None,
    document_status: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> KnowledgeDocumentPage:
    """List versioned documents with bounded filters and pagination."""
    filters = []
    for column, value in (
        (KnowledgeDocument.document_type, document_type),
        (KnowledgeDocument.department, department),
        (KnowledgeDocument.asset_type, asset_type),
        (KnowledgeDocument.region, region),
        (KnowledgeDocument.language, language),
        (KnowledgeDocument.status, document_status),
        (KnowledgeDocument.is_active, is_active),
    ):
        if value is not None:
            filters.append(column == value)
    total = await session.scalar(select(func.count()).select_from(KnowledgeDocument).where(*filters))
    statement = select(KnowledgeDocument).where(*filters).order_by(KnowledgeDocument.created_at.desc()).limit(limit).offset(offset)
    documents = list((await session.scalars(statement)).all())
    return KnowledgeDocumentPage(
        items=[KnowledgeDocumentResponse.from_document(document) for document in documents],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}/chunks", response_model=DocumentChunkPage)
async def get_document_chunks(
    document_id: str,
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentChunkPage:
    """Return safe chunk previews while excluding vectors and full content."""
    exists = await session.scalar(select(KnowledgeDocument.document_id).where(KnowledgeDocument.document_id == document_id))
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    condition = DocumentChunk.document_id == document_id
    total = await session.scalar(select(func.count()).select_from(DocumentChunk).where(condition))
    statement = select(DocumentChunk).where(condition).order_by(DocumentChunk.chunk_number).limit(limit).offset(offset)
    chunks = list((await session.scalars(statement)).all())
    return DocumentChunkPage(
        items=[
            DocumentChunkResponse(
                chunk_number=chunk.chunk_number,
                page_number=chunk.page_number,
                section_title=chunk.section_title,
                token_count=chunk.token_count,
                content_preview=chunk.content[:300] + ("…" if len(chunk.content) > 300 else ""),
                metadata=chunk.metadata_json,
            )
            for chunk in chunks
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_knowledge_document(document_id: str, session: DatabaseSession) -> KnowledgeDocumentResponse:
    """Return safe metadata and stored chunk statistics for one document version."""
    document = (await session.scalars(select(KnowledgeDocument).where(KnowledgeDocument.document_id == document_id))).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    return KnowledgeDocumentResponse.from_document(document)
