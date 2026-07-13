"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import chat, decisions, health, incidents, ingestion
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.utils.exceptions import WasteOpsError

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application_started", environment=settings.app_environment)
    yield
    logger.info("application_stopped")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
for route in (health.router, chat.router, ingestion.router, incidents.router, decisions.router):
    app.include_router(route, prefix="/api")


@app.exception_handler(WasteOpsError)
async def domain_error(_: Request, exc: WasteOpsError) -> JSONResponse:
    """Convert expected domain errors to safe API responses."""
    logger.warning("domain_error", error=str(exc))
    return JSONResponse(status_code=422, content={"detail": str(exc)})
