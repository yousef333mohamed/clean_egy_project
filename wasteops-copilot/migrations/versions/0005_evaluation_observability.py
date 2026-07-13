"""Add prompt, evaluation, tracing, and feedback persistence.

Revision ID: 0005_evaluation_observability
Revises: 0004_retrieval_indexes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_evaluation_observability"
down_revision = "0004_retrieval_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    prompt_status = sa.Enum("DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED", name="prompt_status")
    run_status = sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", "STOPPED_CRITICAL", name="evaluation_run_status")
    feedback_type = sa.Enum("HELPFUL", "NOT_HELPFUL", "INCORRECT_DATA", "MISSING_SOURCE", "BAD_RECOMMENDATION", "UNSAFE", "OTHER", name="feedback_type")
    prompt_status.create(op.get_bind(), checkfirst=True)
    run_status.create(op.get_bind(), checkfirst=True)
    feedback_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("prompt_key", sa.String(80), nullable=False),
        sa.Column("version", sa.String(40), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("description", sa.String(500)), sa.Column("status", prompt_status, nullable=False), sa.Column("created_by", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)), sa.Column("deactivated_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_prompt_versions_prompt_key", "prompt_versions", ["prompt_key"])
    op.create_index("ix_prompt_versions_status", "prompt_versions", ["status"])
    op.create_index("uq_prompt_versions_key_version", "prompt_versions", ["prompt_key", "version"], unique=True)
    op.create_index("uq_prompt_versions_one_active", "prompt_versions", ["prompt_key"], unique=True, postgresql_where=sa.text("status = 'ACTIVE'"))
    op.create_table(
        "evaluation_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(200), nullable=False),
        sa.Column("evaluation_type", sa.String(40), nullable=False), sa.Column("status", run_status, nullable=False),
        sa.Column("dataset_name", sa.String(160), nullable=False), sa.Column("dataset_version", sa.String(40), nullable=False),
        sa.Column("prompt_versions_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("model_configuration_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("total_cases", sa.Integer(), server_default="0", nullable=False), sa.Column("passed_cases", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_cases", sa.Integer(), server_default="0", nullable=False), sa.Column("critical_failures", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metrics_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_evaluation_runs_evaluation_type", "evaluation_runs", ["evaluation_type"])
    op.create_index("ix_evaluation_runs_status", "evaluation_runs", ["status"])
    op.create_table(
        "evaluation_results", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.String(100), nullable=False), sa.Column("category", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("question", sa.Text(), nullable=False), sa.Column("expected_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("actual_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metrics_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("warnings_json", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("failure_reasons_json", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("duration_ms", sa.Float(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_evaluation_results_evaluation_run_id", "evaluation_results", ["evaluation_run_id"])
    op.create_index("ix_evaluation_results_case_id", "evaluation_results", ["case_id"])
    op.create_index("ix_evaluation_results_category", "evaluation_results", ["category"])
    op.create_table(
        "interaction_traces", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("parent_trace_id", sa.String(64)), sa.Column("trace_type", sa.String(50), nullable=False), sa.Column("route", sa.String(160)),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("duration_ms", sa.Float()), sa.Column("provider", sa.String(80)),
        sa.Column("model", sa.String(120)), sa.Column("prompt_key", sa.String(80)), sa.Column("prompt_version", sa.String(40)),
        sa.Column("input_summary_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("output_summary_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metrics_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False), sa.Column("error_category", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name in ("request_id", "parent_trace_id", "trace_type", "status", "expires_at"):
        op.create_index(f"ix_interaction_traces_{name}", "interaction_traces", [name])
    op.create_index("ix_interaction_traces_request_started", "interaction_traces", ["request_id", "started_at"])
    op.create_table(
        "user_feedback", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("request_id", sa.String(64)),
        sa.Column("rating", sa.Integer(), nullable=False), sa.Column("feedback_type", feedback_type, nullable=False), sa.Column("comment", sa.Text()),
        sa.Column("expected_answer", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_user_feedback_rating"),
    )
    op.create_index("ix_user_feedback_request_id", "user_feedback", ["request_id"])
    op.create_index("ix_user_feedback_feedback_type", "user_feedback", ["feedback_type"])


def downgrade() -> None:
    for table in ("user_feedback", "interaction_traces", "evaluation_results", "evaluation_runs", "prompt_versions"):
        op.drop_table(table)
    for name in ("feedback_type", "evaluation_run_status", "prompt_status"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
