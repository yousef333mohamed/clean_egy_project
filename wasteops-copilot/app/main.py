"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import health
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
app.include_router(health.router, prefix="/api")
