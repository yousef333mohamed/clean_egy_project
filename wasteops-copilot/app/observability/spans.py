"""Runtime span representation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import StrEnum


class TraceType(StrEnum):
    RAG_REQUEST = "RAG_REQUEST"
    RETRIEVAL = "RETRIEVAL"
    EMBEDDING = "EMBEDDING"
    LLM_GENERATION = "LLM_GENERATION"
    ANALYTICS_ROUTING = "ANALYTICS_ROUTING"
    ANALYTICS_TOOL = "ANALYTICS_TOOL"
    HYBRID_REQUEST = "HYBRID_REQUEST"
    DECISION_REQUEST = "DECISION_REQUEST"
    OPTION_SCORING = "OPTION_SCORING"
    CONFIDENCE_CALCULATION = "CONFIDENCE_CALCULATION"


@dataclass
class Span:
    trace_id: str
    request_id: str
    parent_trace_id: str | None
    trace_type: str
    started_at: datetime
    attributes: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: dict[str, Any] = field(default_factory=dict)
    status: str = "RUNNING"
    completed_at: datetime | None = None
    duration_ms: float | None = None
    error_category: str | None = None

    def set_metric(self, name: str, value: Any) -> None:
        self.metrics[name] = value

    def set_output(self, **values: Any) -> None:
        self.output_summary.update(values)
