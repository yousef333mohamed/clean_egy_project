"""Application and database health endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    """Return process liveness without requiring downstream services."""
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_environment}


@router.get("/health/database")
async def database_health() -> dict[str, str]:
    """Return database readiness without leaking connection details."""
    try:
        await check_database_connection()
    except Exception as exc:
        logger.error("database_health_check_failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service is unavailable") from exc
    return {"status": "healthy", "database": "connected"}
