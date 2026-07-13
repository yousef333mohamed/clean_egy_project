"""Shared retrieval projection and evidence conversion."""

from typing import Any

from sqlalchemy import literal

from app.models import DocumentChunk, KnowledgeDocument
from app.schemas.retrieval import RetrievedEvidence


def evidence_columns(score: Any | None = None) -> tuple[Any, ...]:
    return (
        DocumentChunk.id.label("chunk_id"),
        DocumentChunk.document_id,
        DocumentChunk.source_filename,
        KnowledgeDocument.title.label("document_title"),
        DocumentChunk.document_type,
        DocumentChunk.department,
        DocumentChunk.asset_type,
        DocumentChunk.region,
        DocumentChunk.language,
        DocumentChunk.version,
        DocumentChunk.effective_date,
        KnowledgeDocument.expiration_date,
        KnowledgeDocument.authority_level,
        DocumentChunk.page_number,
        DocumentChunk.section_title,
        DocumentChunk.chunk_number,
        DocumentChunk.content,
        DocumentChunk.content_hash,
        KnowledgeDocument.is_synthetic,
        (score if score is not None else literal(0.0)).label("raw_score"),
    )


def row_to_evidence(row: Any, *, vector_score: float = 0, keyword_score: float = 0) -> RetrievedEvidence:
    data = row._mapping
    content = data["content"]
    final = vector_score or keyword_score
    return RetrievedEvidence(
        chunk_id=str(data["chunk_id"]),
        document_id=data["document_id"],
        source_filename=data["source_filename"],
        document_title=data["document_title"],
        document_type=data["document_type"],
        department=data["department"],
        asset_type=data["asset_type"],
        region=data["region"],
        language=data["language"],
        version=data["version"],
        effective_date=data["effective_date"],
        expiration_date=data["expiration_date"],
        authority_level=data["authority_level"],
        page_number=data["page_number"],
        section_title=data["section_title"],
        chunk_number=data["chunk_number"],
        content=content,
        content_preview=content[:300] + ("…" if len(content) > 300 else ""),
        vector_score=vector_score,
        keyword_score=keyword_score,
        final_score=final,
        is_synthetic=bool(data["is_synthetic"]),
        content_hash=data["content_hash"],
    )
