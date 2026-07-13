"""Strict CORS configuration parsing."""

from app.core.config import Settings


def allowed_origins(settings: Settings) -> list[str]:
    """Return validated exact origins."""
    return [origin.strip().rstrip("/") for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
