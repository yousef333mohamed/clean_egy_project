"""Add authority metadata and a keyword-search GIN index.

Revision ID: 0004_retrieval_indexes
Revises: 0003_document_ingestion
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_retrieval_indexes"
down_revision = "0003_document_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add filterable authority fields and language-neutral full-text index."""
    op.add_column("knowledge_documents", sa.Column("is_synthetic", sa.Boolean(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("authority_level", sa.String(30), server_default="unknown", nullable=False))
    op.add_column("knowledge_documents", sa.Column("expiration_date", sa.Date(), nullable=True))
    for column in ("is_synthetic", "authority_level", "expiration_date"):
        op.create_index(f"ix_knowledge_documents_{column}", "knowledge_documents", [column])
    op.create_index(
        "ix_document_chunks_content_fts_simple",
        "document_chunks",
        [sa.text("to_tsvector('simple', coalesce(content, ''))")],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Remove Step 5 authority fields and keyword index."""
    op.drop_index("ix_document_chunks_content_fts_simple", table_name="document_chunks", postgresql_using="gin")
    for column in reversed(("is_synthetic", "authority_level", "expiration_date")):
        op.drop_index(f"ix_knowledge_documents_{column}", table_name="knowledge_documents")
        op.drop_column("knowledge_documents", column)
