"""Application and database health endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.logging import get_logger
from app.prompts.versioning import PROMPT_KEYS

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    """Return process liveness without requiring downstream services."""
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_environment}


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Confirm only that the application process can answer requests."""
    return {"status": "alive"}


@router.get("/health/database")
async def database_health() -> dict[str, str]:
    """Return database readiness without leaking connection details."""
    try:
        await check_database_connection()
    except Exception as exc:
        logger.error("database_health_check_failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service is unavailable") from exc
    return {"status": "healthy", "database": "connected"}


@router.get("/health/ready")
async def readiness() -> dict[str, object]:
    """Check required local dependencies without exposing infrastructure."""
    settings = get_settings()
    checks: dict[str, str] = {"configuration": "healthy", "prompts": "healthy" if PROMPT_KEYS else "unavailable"}
    try:
        await check_database_connection()
        checks["database"] = "healthy"
        if settings.redis_required:
            from redis.asyncio import from_url

            client = from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
            try:
                await client.ping()
                checks["redis"] = "healthy"
            finally:
                await client.aclose()
    except Exception as exc:
        logger.warning("readiness_check_failed", category=type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status": "not_ready", "checks": {**checks, "required_dependency": "unavailable"}}
        ) from exc
    return {"status": "ready", "checks": checks}


@router.get("/health/version")
async def version() -> dict[str, str]:
    settings = get_settings()
    return {
        "version": settings.app_release_version,
        "commit_sha": settings.app_commit_sha,
        "build_time": settings.app_build_time,
        "environment": settings.app_environment,
    }
