"""Ingestion routing safety and discovery contract tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def _settings(data_dir: Path, *, enabled: bool = True) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@database:5432/test",
        database_sync_url="postgresql+psycopg://test:test@database:5432/test",
        data_dir=str(data_dir),
        enable_ingestion_api=enabled,
    )


def test_file_discovery_response_schema(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "smart_bins(1).csv").write_text("bin_id\n", encoding="utf-8")
    app.dependency_overrides[get_settings] = lambda: _settings(tmp_path)
    try:
        response = TestClient(app).get("/api/ingestion/files")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    smart_bins = next(item for item in response.json() if item["dataset"] == "smart_bins")
    assert smart_bins == {
        "dataset": "smart_bins",
        "filename": "smart_bins(1).csv",
        "size_bytes": (raw / "smart_bins(1).csv").stat().st_size,
        "available": True,
    }


def test_unknown_and_path_traversal_datasets_return_404(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings(tmp_path)
    try:
        client = TestClient(app)
        assert client.post("/api/ingestion/csv/unknown", json={}).status_code == 404
        assert client.post("/api/ingestion/csv/..%2Fsmart_bins", json={}).status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_disabled_ingestion_api_returns_403(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings(tmp_path, enabled=False)
    try:
        response = TestClient(app).post("/api/ingestion/csv/smart_bins", json={})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403
