"""Provider-neutral, aggressively scrubbed error event interface."""

from typing import Protocol

from app.observability.sanitization import sanitize


class ErrorMonitor(Protocol):
    def capture(self, error: Exception, context: dict[str, object]) -> None: ...


def safe_error_context(context: dict[str, object]) -> dict[str, object]:
    """Keep only operational identifiers after the shared sanitizer removes secrets/content."""
    allowed = {"release", "environment", "request_id", "trace_id", "route", "actor_subject_hash", "error_category"}
    return sanitize({key: value for key, value in context.items() if key in allowed})
