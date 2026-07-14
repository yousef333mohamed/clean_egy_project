"""Async context-manager tracer with safe persistence and context propagation."""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.interaction_trace import InteractionTrace
from app.observability.context import parent_trace_id_var, request_id_var, trace_id_var
from app.observability.sanitization import sanitize
from app.observability.spans import Span

logger = get_logger(__name__)


class Tracer:
    """Capture only allow-listed summaries; full content is never persisted."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings or get_settings()
        self.completed_spans: list[InteractionTrace] = []

    @asynccontextmanager
    async def span(self, trace_type: str, attributes: dict[str, Any] | None = None) -> AsyncIterator[Span]:
        if not self.settings.tracing_enabled:
            yield Span(str(uuid.uuid4()), request_id_var.get() or str(uuid.uuid4()), trace_id_var.get(), trace_type, datetime.now(UTC))
            return
        parent_id = trace_id_var.get()
        trace_id = str(uuid.uuid4())
        request_id = request_id_var.get() or str(uuid.uuid4())
        started = datetime.now(UTC)
        runtime = Span(trace_id, request_id, parent_id, trace_type, started, sanitize(attributes or {}))
        request_token = request_id_var.set(request_id)
        parent_token = parent_trace_id_var.set(parent_id)
        trace_token = trace_id_var.set(trace_id)
        timer = time.perf_counter()
        try:
            yield runtime
            runtime.status = "SUCCESS"
        except Exception as exc:
            runtime.status = "FAILED"
            runtime.error_category = type(exc).__name__[:100]
            raise
        finally:
            runtime.completed_at = datetime.now(UTC)
            runtime.duration_ms = (time.perf_counter() - timer) * 1000
            record = self._to_record(runtime)
            self.completed_spans.append(record)
            await self._store(record)
            trace_id_var.reset(trace_token)
            parent_trace_id_var.reset(parent_token)
            request_id_var.reset(request_token)

    async def _store(self, record: InteractionTrace) -> None:
        """Persist a trace independently and never affect the traced workflow."""
        try:
            async with self.session_factory() as trace_session:
                try:
                    trace_session.add(record)
                    await trace_session.commit()
                except Exception:
                    await trace_session.rollback()
                    raise
        except Exception:
            logger.exception(
                "interaction_trace_storage_failed",
                trace_type=record.trace_type,
                request_id=record.request_id,
                status=record.status,
            )

    def _to_record(self, span: Span) -> InteractionTrace:
        attrs = span.attributes
        return InteractionTrace(
            id=uuid.UUID(span.trace_id),
            request_id=span.request_id,
            parent_trace_id=span.parent_trace_id,
            trace_type=span.trace_type,
            route=attrs.get("route"),
            status=span.status,
            started_at=span.started_at,
            completed_at=span.completed_at,
            duration_ms=span.duration_ms,
            provider=attrs.get("provider"),
            model=attrs.get("model"),
            prompt_key=attrs.get("prompt_key"),
            prompt_version=attrs.get("prompt_version"),
            input_summary_json=sanitize(span.input_summary) if self.settings.trace_store_inputs else {},
            output_summary_json=sanitize(span.output_summary) if self.settings.trace_store_outputs else {},
            metrics_json=sanitize(
                {**span.metrics, **{k: v for k, v in attrs.items() if k not in {"route", "provider", "model", "prompt_key", "prompt_version"}}}
            ),
            error_category=span.error_category,
            expires_at=span.started_at + timedelta(days=self.settings.trace_retention_days),
        )
