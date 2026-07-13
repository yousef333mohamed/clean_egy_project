"""Private WasteOps model-serving application."""

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request

from app.api.routes import health, models, monitoring, predictions
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # The readiness route enforces required approved models; startup never downloads artifacts.
    yield


app = FastAPI(title=settings.ml_service_name, docs_url=None if settings.ml_service_env.casefold() == "production" else "/docs", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


for router in (health.router, predictions.router, models.router, monitoring.router):
    app.include_router(router, prefix=settings.ml_service_api_prefix)
