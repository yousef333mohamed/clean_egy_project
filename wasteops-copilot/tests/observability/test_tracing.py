"""Trace propagation, retention, failure, and credential redaction."""

from app.core.config import Settings
from app.observability.context import current_trace_context
from app.observability.sanitization import REDACTED, sanitize
from app.observability.tracer import Tracer


class TraceSession:
    def __init__(self, *, commit_error=None):
        self.added = []
        self.committed = False
        self.rolled_back = False
        self.commit_error = commit_error

    def add(self, record):
        self.added.append(record)

    async def commit(self):
        if self.commit_error:
            raise self.commit_error
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class TraceSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_args):
        return False


def session_factory(session):
    return lambda: TraceSessionContext(session)


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://x:x@db/x", "database_sync_url": "postgresql+psycopg://x:x@db/x"}
    values.update(updates)
    return Settings(**values)


def test_sanitization_redacts_credentials_and_marks_truncation():
    value = sanitize({"authorization": "Bearer top-secret-token", "database_url": "postgresql://u:p@host/db", "text": "x" * 1100})
    assert value["authorization"] == REDACTED and value["database_url"] == REDACTED and "TRUNCATED" in value["text"]


async def test_successful_analytics_trace_uses_dedicated_write_session():
    trace_session = TraceSession()
    tracer = Tracer(session_factory(trace_session), settings(trace_store_inputs=False, trace_store_outputs=False))
    async with tracer.span("RAG_REQUEST", {"route": "/api/chat"}) as parent:
        parent.input_summary["password"] = "not-stored"
        async with tracer.span("RETRIEVAL", {"retrieved_chunks": 2}):
            assert current_trace_context()["parent_trace_id"] == parent.trace_id
    child, outer = tracer.completed_spans
    assert child.parent_trace_id == outer.id.hex or child.parent_trace_id == str(outer.id)
    assert outer.input_summary_json == {} and outer.status == "SUCCESS" and outer.duration_ms >= 0
    assert outer.expires_at > outer.started_at
    assert trace_session.added == [child, outer] and trace_session.committed


async def test_failed_span_records_category():
    trace_session = TraceSession()
    tracer = Tracer(session_factory(trace_session), settings())
    try:
        async with tracer.span("RETRIEVAL"):
            raise RuntimeError("private stack")
    except RuntimeError:
        pass
    assert tracer.completed_spans[0].status == "FAILED" and tracer.completed_spans[0].error_category == "RuntimeError"


async def test_trace_storage_failure_is_fail_open():
    trace_session = TraceSession(commit_error=RuntimeError("trace database unavailable"))
    tracer = Tracer(session_factory(trace_session), settings())

    async with tracer.span("ANALYTICS_TOOL") as span:
        span.set_metric("rows", 1)

    assert tracer.completed_spans[0].status == "SUCCESS"
    assert trace_session.rolled_back
