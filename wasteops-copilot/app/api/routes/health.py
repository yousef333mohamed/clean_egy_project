"""Health endpoint."""

from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return process liveness without requiring downstream services."""
    return {"status": "ok", "service": get_settings().app_name, "environment": get_settings().app_environment}
