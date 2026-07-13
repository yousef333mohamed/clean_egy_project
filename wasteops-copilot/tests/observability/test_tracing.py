"""Trace propagation, retention, failure, and credential redaction."""

from app.core.config import Settings
from app.observability.context import current_trace_context
from app.observability.sanitization import REDACTED, sanitize
from app.observability.tracer import Tracer


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://x:x@db/x", "database_sync_url": "postgresql+psycopg://x:x@db/x"}
    values.update(updates)
    return Settings(**values)


def test_sanitization_redacts_credentials_and_marks_truncation():
    value = sanitize({"authorization": "Bearer top-secret-token", "database_url": "postgresql://u:p@host/db", "text": "x" * 1100})
    assert value["authorization"] == REDACTED and value["database_url"] == REDACTED and "TRUNCATED" in value["text"]


async def test_parent_child_spans_and_safe_storage_defaults():
    tracer = Tracer(settings=settings(trace_store_inputs=False, trace_store_outputs=False))
    async with tracer.span("RAG_REQUEST", {"route": "/api/chat"}) as parent:
        parent.input_summary["password"] = "not-stored"
        async with tracer.span("RETRIEVAL", {"retrieved_chunks": 2}):
            assert current_trace_context()["parent_trace_id"] == parent.trace_id
    child, outer = tracer.completed_spans
    assert child.parent_trace_id == outer.id.hex or child.parent_trace_id == str(outer.id)
    assert outer.input_summary_json == {} and outer.status == "SUCCESS" and outer.duration_ms >= 0
    assert outer.expires_at > outer.started_at


async def test_failed_span_records_category():
    tracer = Tracer(settings=settings())
    try:
        async with tracer.span("RETRIEVAL"):
            raise RuntimeError("private stack")
    except RuntimeError:
        pass
    assert tracer.completed_spans[0].status == "FAILED" and tracer.completed_spans[0].error_category == "RuntimeError"
