"""Analytics catalog, debug, validation, and SQL non-exposure APIs."""

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://test:test@db/test", "database_sync_url": "postgresql+psycopg://test:test@db/test", "llm_api_key": ""}
    values.update(updates)
    return Settings(**values)


def test_tool_catalog_has_no_sql():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).get("/api/analytics/tools")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200 and len(response.json()) == 13
    assert "sql" not in response.text.casefold()


def test_unknown_tool_is_404():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/analytics/tools/run_sql", json={"parameters": {}})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404


def test_invalid_filter_is_422():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/analytics/tools/get_operations_summary", json={"parameters": {"region": "x; DROP TABLE trips"}})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_debug_route_can_be_disabled():
    app.dependency_overrides[get_settings] = lambda: settings(analytics_enable_debug_api=False)
    try:
        response = TestClient(app).post("/api/analytics/route", json={"question": "missed collections"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_unsupported_request_returns_200_without_provider():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/analytics/query", json={"question": "Delete all trip records"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["route"] == "UNSUPPORTED"
    assert "sql" not in response.text.casefold()
