"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import (
    analytics,
    audit,
    auth,
    chat,
    decisions,
    documents,
    evaluation,
    feedback,
    health,
    ingestion,
    jobs,
    metrics,
    ml,
    prompts,
    retrieval,
    traces,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.security.cors import allowed_origins
from app.security.headers import SecurityHeadersMiddleware
from app.security.middleware import RequestContextMiddleware
from app.security.rate_limit import RateLimitMiddleware
from app.security.request_limits import RequestSizeLimitMiddleware
from app.security.trusted_hosts import trusted_hosts

settings = get_settings()
configure_logging(settings.log_level, settings.app_environment)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log process lifecycle without creating database schema."""
    logger.info("application_started", environment=settings.app_environment)
    yield
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_release_version,
    lifespan=lifespan,
    docs_url=None if settings.app_environment.casefold() == "production" else "/docs",
    redoc_url=None if settings.app_environment.casefold() == "production" else "/redoc",
    openapi_url=None if settings.app_environment.casefold() == "production" else "/openapi.json",
)
app.state.settings = settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(settings),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts(settings))
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
app.add_middleware(RateLimitMiddleware, settings=settings)
app.add_middleware(RequestContextMiddleware)
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(retrieval.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(decisions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(traces.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(metrics.router)
app.include_router(ml.router, prefix="/api")
app.include_router(ml.prediction_router, prefix="/api")
