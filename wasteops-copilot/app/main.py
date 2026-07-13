"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, chat, decisions, documents, evaluation, feedback, health, ingestion, prompts, retrieval, traces
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log process lifecycle without creating database schema."""
    logger.info("application_started", environment=settings.app_environment)
    yield
    logger.info("application_stopped")


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.include_router(health.router, prefix="/api")
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
