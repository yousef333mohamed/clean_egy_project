"""Embedded knowledge-base chunk persistence model."""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.models.base import Base


class DocumentChunk(Base):
    """A structure-aware chunk and its OpenAI-compatible embedding."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_number", name="uq_document_chunks_document_chunk"),
        CheckConstraint("length(btrim(content)) > 0", name="ck_document_chunks_content_not_empty"),
        CheckConstraint("chunk_number >= 0", name="ck_document_chunks_chunk_number_nonnegative"),
        CheckConstraint("token_count > 0", name="ck_document_chunks_token_count_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    asset_type: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(get_settings().vector_dimensions), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks", lazy="raise")


from app.models.knowledge_document import KnowledgeDocument  # noqa: E402
