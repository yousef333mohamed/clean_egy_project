from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app


def test_private_endpoint_rejects_missing_service_identity():
    response = TestClient(app).post("/api/plans/optimize", json={})
    assert response.status_code == 403
    assert response.headers["X-Request-ID"]


def test_health_reports_solver_without_authentication(monkeypatch):
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(service_token="secret"))
    response = TestClient(app).get("/api/health/ready")
    assert response.status_code == 200
    assert response.json()["solver"] == "Google OR-Tools"
