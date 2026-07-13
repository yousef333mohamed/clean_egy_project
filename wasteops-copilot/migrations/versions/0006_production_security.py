"""Add immutable audit storage.

Revision ID: 0006_production_security
Revises: 0005_evaluation_observability
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_production_security"
down_revision = "0005_evaluation_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("actor_subject_hash", sa.String(64)),
        sa.Column("actor_roles", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("request_id", sa.String(64)),
        sa.Column("route", sa.String(255), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(80)),
        sa.Column("resource_id_hash", sa.String(64)),
        sa.Column("source_ip_hash", sa.String(64)),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    for column in ("event_type", "actor_subject_hash", "request_id", "created_at"):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column])
    op.create_index("ix_audit_events_actor_created", "audit_events", ["actor_subject_hash", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_events")
