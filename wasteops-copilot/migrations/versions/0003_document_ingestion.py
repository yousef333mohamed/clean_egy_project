"""Add versioned knowledge documents and production chunk metadata.

Revision ID: 0003_document_ingestion
Revises: 0002_csv_ingestion
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_document_ingestion"
down_revision = "0002_csv_ingestion"
branch_labels = None
depends_on = None

document_status = postgresql.ENUM(
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "COMPLETED_WITH_WARNINGS",
    "FAILED",
    "SKIPPED_DUPLICATE",
    "REPLACED",
    name="document_status",
    create_type=False,
)


def upgrade() -> None:
    """Create document history, enrich chunks, and add a cosine HNSW index."""
    document_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.String(36), nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("original_path", sa.String(1024), nullable=False),
        sa.Column("file_extension", sa.String(10), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("document_type", sa.String(80), nullable=True),
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("asset_type", sa.String(120), nullable=True),
        sa.Column("region", sa.String(120), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("version", sa.String(40), nullable=True),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column("total_pages", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_characters", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_chunks", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("replaced_by_document_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["replaced_by_document_id"], ["knowledge_documents.document_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    for column in ("document_id", "document_type", "department", "asset_type", "region", "effective_date", "language", "status", "is_active"):
        op.create_index(f"ix_knowledge_documents_{column}", "knowledge_documents", [column])
    op.create_index("ix_knowledge_documents_file_hash", "knowledge_documents", ["file_hash"])
    op.create_index("ix_knowledge_documents_relative_path", "knowledge_documents", ["original_path"])

    op.add_column("document_chunks", sa.Column("language", sa.String(20), server_default="unknown", nullable=False))
    op.add_column("document_chunks", sa.Column("page_number", sa.Integer(), nullable=True))
    op.add_column("document_chunks", sa.Column("section_title", sa.String(500), nullable=True))
    op.add_column("document_chunks", sa.Column("content_hash", sa.String(64), server_default="", nullable=False))
    op.add_column("document_chunks", sa.Column("token_count", sa.Integer(), server_default="1", nullable=False))
    op.add_column("document_chunks", sa.Column("embedding_model", sa.String(120), server_default="text-embedding-3-small", nullable=False))
    op.add_column("document_chunks", sa.Column("embedding_dimensions", sa.Integer(), server_default="1536", nullable=False))
    op.add_column("document_chunks", sa.Column("embedded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.alter_column("document_chunks", "document_type", type_=sa.String(80), existing_type=sa.String(40), existing_nullable=True)
    op.create_foreign_key(
        "fk_document_chunks_document_id",
        "document_chunks",
        "knowledge_documents",
        ["document_id"],
        ["document_id"],
        ondelete="CASCADE",
    )
    for column in ("document_type", "department", "asset_type", "region", "effective_date", "language", "content_hash"):
        op.create_index(f"ix_document_chunks_{column}", "document_chunks", [column])
    op.create_check_constraint("ck_document_chunks_token_count_positive", "document_chunks", "token_count > 0")
    op.create_index(
        "ix_document_chunks_embedding_hnsw_cosine",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"m": 16, "ef_construction": 64},
    )


def downgrade() -> None:
    """Remove Step 4 document metadata and vector search index."""
    op.drop_index("ix_document_chunks_embedding_hnsw_cosine", table_name="document_chunks", postgresql_using="hnsw")
    op.drop_constraint("ck_document_chunks_token_count_positive", "document_chunks", type_="check")
    for column in reversed(("document_type", "department", "asset_type", "region", "effective_date", "language", "content_hash")):
        op.drop_index(f"ix_document_chunks_{column}", table_name="document_chunks")
    op.drop_constraint("fk_document_chunks_document_id", "document_chunks", type_="foreignkey")
    op.alter_column("document_chunks", "document_type", type_=sa.String(40), existing_type=sa.String(80), existing_nullable=True)
    for column in ("embedded_at", "embedding_dimensions", "embedding_model", "token_count", "content_hash", "section_title", "page_number", "language"):
        op.drop_column("document_chunks", column)
    op.drop_table("knowledge_documents")
    document_status.drop(op.get_bind(), checkfirst=True)
