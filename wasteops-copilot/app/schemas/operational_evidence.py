"""Structured evidence returned by approved database tools."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.analytics.enums import EvidenceSourceType


class DataPeriod(BaseModel):
    start: str | None = None
    end: str | None = None


class OperationalEvidence(BaseModel):
    evidence_id: str
    source_type: EvidenceSourceType = EvidenceSourceType.DATABASE
    tool_name: str
    metric: str | None = None
    description: str
    filters: dict[str, Any]
    columns: list[str]
    rows: list[dict[str, Any]]
    record_count: int
    data_period: DataPeriod
    generated_at: datetime
    notes: list[str] = Field(default_factory=list)
    aggregation_definitions: dict[str, str] = Field(default_factory=dict)
