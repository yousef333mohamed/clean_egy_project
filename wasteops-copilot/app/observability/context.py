"""Context-local trace identifiers propagated across async tasks."""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
parent_trace_id_var: ContextVar[str | None] = ContextVar("parent_trace_id", default=None)


def current_trace_context() -> dict[str, str | None]:
    return {"request_id": request_id_var.get(), "trace_id": trace_id_var.get(), "parent_trace_id": parent_trace_id_var.get()}
