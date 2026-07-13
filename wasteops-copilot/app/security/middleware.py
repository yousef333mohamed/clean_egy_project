"""Request correlation, metrics, and sanitized audit integration."""

import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from app.audit.middleware import audit_values
from app.audit.service import record_audit_event
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.observability.prometheus import AUTH_FAILURES, AUTHZ_DENIALS, HTTP_LATENCY, HTTP_REQUESTS

logger = get_logger(__name__)
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request.state.request_id = incoming if SAFE_REQUEST_ID.fullmatch(incoming) else str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        route = getattr(request.scope.get("route"), "path", "unmatched")
        HTTP_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        HTTP_LATENCY.labels(request.method, route).observe(duration_ms / 1000)
        if response.status_code == 401:
            AUTH_FAILURES.inc()
        elif response.status_code == 403:
            AUTHZ_DENIALS.inc()
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(
            "http_request",
            service="backend",
            environment=request.app.state.settings.app_environment,
            request_id=request.state.request_id,
            route=route,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        values = audit_values(request, response)
        if values:
            try:
                async with AsyncSessionLocal() as session:
                    await record_audit_event(session, **values)
            except Exception:
                logger.warning("audit_persistence_failed", request_id=request.state.request_id)
        return response
