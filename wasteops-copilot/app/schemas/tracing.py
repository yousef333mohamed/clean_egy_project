"""Safe trace API responses."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TraceSummary(BaseModel):
    id: uuid.UUID
    request_id: str
    parent_trace_id: str | None
    trace_type: str
    route: str | None
    status: str
    started_at: datetime
    duration_ms: float | None
    provider: str | None
    model: str | None
    prompt_key: str | None
    prompt_version: str | None
    metrics: dict[str, Any] = Field(default_factory=dict)
    error_category: str | None


class TracePage(BaseModel):
    items: list[TraceSummary]
    offset: int
    limit: int
