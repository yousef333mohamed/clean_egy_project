"""Add approval-gated optimization plans.

Revision ID: 0008_route_optimization
Revises: 0007_ml_platform
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_route_optimization"
down_revision = "0007_ml_platform"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "optimization_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("solver_plan_id", sa.String(64), nullable=False, unique=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("request_json", postgresql.JSONB(), nullable=False),
        sa.Column("result_json", postgresql.JSONB(), nullable=False),
        sa.Column("review_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("review_notes", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    for column in ("solver_plan_id", "request_id", "plan_date", "status", "review_status"):
        op.create_index(f"ix_optimization_plans_{column}", "optimization_plans", [column])


def downgrade():
    op.drop_table("optimization_plans")
