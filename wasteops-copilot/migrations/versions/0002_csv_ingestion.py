"""Add CSV ingestion audit tables and nullable source measurements.

Revision ID: 0002_csv_ingestion
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_csv_ingestion"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

ingestion_status = postgresql.ENUM(
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "COMPLETED_WITH_ERRORS",
    "FAILED",
    "SKIPPED_DUPLICATE",
    "DRY_RUN_COMPLETED",
    name="ingestion_status",
    create_type=False,
)


def upgrade() -> None:
    """Create tracking tables and preserve valid missing source values."""
    ingestion_status.create(op.get_bind(), checkfirst=True)
    op.alter_column("smart_bin_readings", "fill_level_pct", existing_type=sa.Numeric(5, 2), nullable=True)
    op.alter_column("smart_bin_readings", "waste_weight_kg", existing_type=sa.Numeric(12, 3), nullable=True)
    op.alter_column("workforce_attendance", "performance_score", existing_type=sa.Numeric(5, 2), nullable=True)

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_name", sa.String(80), nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", ingestion_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("inserted_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicate_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dry_run", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_dataset_name", "ingestion_runs", ["dataset_name"])
    op.create_index("ix_ingestion_runs_file_hash", "ingestion_runs", ["file_hash"])
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])
    op.create_index(
        "uq_ingestion_runs_successful_file",
        "ingestion_runs",
        ["dataset_name", "file_hash"],
        unique=True,
        postgresql_where=sa.text("status IN ('COMPLETED', 'COMPLETED_WITH_ERRORS') AND dry_run = false"),
    )
    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_name", sa.String(80), nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(80), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("raw_record", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_errors_ingestion_run_id", "ingestion_errors", ["ingestion_run_id"])
    op.create_index("ix_ingestion_errors_dataset_name", "ingestion_errors", ["dataset_name"])


def downgrade() -> None:
    """Remove tracking tables and restore the Step 2 nullability."""
    op.drop_table("ingestion_errors")
    op.drop_table("ingestion_runs")
    op.alter_column("workforce_attendance", "performance_score", existing_type=sa.Numeric(5, 2), nullable=False)
    op.alter_column("smart_bin_readings", "waste_weight_kg", existing_type=sa.Numeric(12, 3), nullable=False)
    op.alter_column("smart_bin_readings", "fill_level_pct", existing_type=sa.Numeric(5, 2), nullable=False)
    ingestion_status.drop(op.get_bind(), checkfirst=True)
