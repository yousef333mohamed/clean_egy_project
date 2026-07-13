import logging
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.service_name, docs_url=None if settings.environment == "production" else "/docs")
app.include_router(router, prefix="/api")

logger = logging.getLogger("optimization_service")


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "optimization_request method=%s path=%s status=%s duration_ms=%s request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        round((time.perf_counter() - started) * 1000),
        request_id,
    )
    return response
