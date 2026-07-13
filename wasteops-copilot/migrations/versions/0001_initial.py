"""Initial pgvector and WasteOps schema."""

from alembic import op
from app.core.database import Base
from app.models import attendance, bin, document, environment, operation, trip, truck, workforce  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
