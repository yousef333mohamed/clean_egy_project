"""Persistent audit record for one CSV ingestion attempt."""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IngestionStatus(str, enum.Enum):
    """Lifecycle states exposed by the ingestion API."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"
    DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED"


class IngestionRun(Base):
    """Counts, timings, and provenance for an ingestion attempt."""

    __tablename__ = "ingestion_runs"
    __table_args__ = (
        Index(
            "uq_ingestion_runs_successful_file",
            "dataset_name",
            "file_hash",
            unique=True,
            postgresql_where=text("status IN ('COMPLETED', 'COMPLETED_WITH_ERRORS') AND dry_run = false"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus, name="ingestion_status"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inserted_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)

    errors: Mapped[list["IngestionError"]] = relationship(back_populates="run", cascade="all, delete-orphan", lazy="raise")


from app.models.ingestion_error import IngestionError  # noqa: E402
