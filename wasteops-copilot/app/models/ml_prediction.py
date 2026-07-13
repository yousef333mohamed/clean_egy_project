"""Safe ML lineage, prediction, data-quality, drift, and performance records."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MLPredictionRun(Base):
    __tablename__ = "ml_prediction_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    model_name: Mapped[str] = mapped_column(String(80), index=True)
    model_version: Mapped[str] = mapped_column(String(80))
    entity_count: Mapped[int] = mapped_column(Integer)
    is_backfill: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ml_prediction_runs.id", ondelete="CASCADE"), index=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    model_name: Mapped[str] = mapped_column(String(80), index=True)
    model_version: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(160), index=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    feature_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    prediction_horizon: Mapped[str | None] = mapped_column(String(40))
    prediction_value: Mapped[float] = mapped_column(Float)
    predicted_class: Mapped[bool | None] = mapped_column(Boolean)
    threshold: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(30))
    input_feature_version: Mapped[str] = mapped_column(String(40))
    warnings_json: Mapped[list] = mapped_column(JSON, default=list)
    safe_feature_hash: Mapped[str | None] = mapped_column(String(64))
    explanation_json: Mapped[list] = mapped_column(JSON, default=list)
    is_backfill: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MLModelVersion(Base):
    __tablename__ = "ml_model_versions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(80), index=True)
    model_version: Mapped[str] = mapped_column(String(80), index=True)
    stage: Mapped[str] = mapped_column(String(30), index=True)
    training_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    training_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    feature_version: Mapped[str] = mapped_column(String(40))
    code_commit: Mapped[str] = mapped_column(String(64))
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    decision_threshold: Mapped[float | None] = mapped_column(Float)
    artifact_checksum: Mapped[str] = mapped_column(String(64))
    approval_status: Mapped[str] = mapped_column(String(30))
    promoted_by: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class _MLReportMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(80), index=True)
    model_version: Mapped[str] = mapped_column(String(80))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    severity: Mapped[str] = mapped_column(String(30))
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MLDataQualityEvent(_MLReportMixin, Base):
    __tablename__ = "ml_data_quality_events"
    event_type: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text)


class MLDriftReport(_MLReportMixin, Base):
    __tablename__ = "ml_drift_reports"
    drift_detected: Mapped[bool] = mapped_column(Boolean)


class MLPerformanceReport(_MLReportMixin, Base):
    __tablename__ = "ml_performance_reports"
    confirmed_outcome_count: Mapped[int] = mapped_column(Integer)
