"""Add safe ML lineage and monitoring tables.

Revision ID: 0007_ml_platform
Revises: 0006_production_security
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_ml_platform"
down_revision = "0006_production_security"
branch_labels = None
depends_on = None


def _report_columns():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    op.create_table(
        "ml_prediction_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("is_backfill", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "ml_predictions",
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_prediction_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.String(160), nullable=False),
        sa.Column("prediction_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("feature_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prediction_horizon", sa.String(40)),
        sa.Column("prediction_value", sa.Float(), nullable=False),
        sa.Column("predicted_class", sa.Boolean()),
        sa.Column("threshold", sa.Float()),
        sa.Column("risk_level", sa.String(30)),
        sa.Column("input_feature_version", sa.String(40), nullable=False),
        sa.Column("warnings_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("safe_feature_hash", sa.String(64)),
        sa.Column("explanation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_backfill", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "ml_model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.Column("training_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("training_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("feature_version", sa.String(40), nullable=False),
        sa.Column("code_commit", sa.String(64), nullable=False),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("decision_threshold", sa.Float()),
        sa.Column("artifact_checksum", sa.String(64), nullable=False),
        sa.Column("approval_status", sa.String(30), nullable=False),
        sa.Column("promoted_by", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("model_name", "model_version", name="uq_ml_model_version"),
    )
    op.create_table(
        "ml_data_quality_events", *_report_columns(), sa.Column("event_type", sa.String(80), nullable=False), sa.Column("details", sa.Text(), nullable=False)
    )
    op.create_table("ml_drift_reports", *_report_columns(), sa.Column("drift_detected", sa.Boolean(), nullable=False))
    op.create_table("ml_performance_reports", *_report_columns(), sa.Column("confirmed_outcome_count", sa.Integer(), nullable=False))
    for table in ("ml_prediction_runs", "ml_predictions", "ml_model_versions", "ml_data_quality_events", "ml_drift_reports", "ml_performance_reports"):
        op.create_index(f"ix_{table}_model_name", table, ["model_name"])


def downgrade() -> None:
    for table in ("ml_performance_reports", "ml_drift_reports", "ml_data_quality_events", "ml_model_versions", "ml_predictions", "ml_prediction_runs"):
        op.drop_table(table)
