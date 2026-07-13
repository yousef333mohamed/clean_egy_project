"""Health endpoint tests that do not require a live database."""

from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.api.routes import health as health_routes
from app.main import app


async def test_application_health() -> None:
    """The liveness route remains independent of downstream services."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_database_health_success(monkeypatch) -> None:
    """A successful database probe returns the documented payload."""
    monkeypatch.setattr(health_routes, "check_database_connection", AsyncMock(return_value=None))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


async def test_database_health_failure_is_safe(monkeypatch) -> None:
    """Connection failures return 503 without exposing their details."""
    secret_error = "postgresql://user:secret@internal/database"
    monkeypatch.setattr(health_routes, "check_database_connection", AsyncMock(side_effect=RuntimeError(secret_error)))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health/database")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database service is unavailable"}
    assert secret_error not in response.text
