"""Document API safety and public-schema tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def settings(path: Path, *, enabled: bool = True) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        documents_directory=str(path),
        data_dir=str(path.parent),
        enable_document_ingestion_api=enabled,
    )


def test_document_discovery_never_exposes_absolute_path(tmp_path: Path) -> None:
    (tmp_path / "manual.md").write_text("# Demo", encoding="utf-8")
    app.dependency_overrides[get_settings] = lambda: settings(tmp_path)
    try:
        response = TestClient(app).get("/api/documents/files")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["relative_path"] == "manual.md"
    assert "path" not in response.json()[0]


def test_disabled_write_endpoint_returns_403(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings] = lambda: settings(tmp_path, enabled=False)
    try:
        response = TestClient(app).post("/api/documents/validate", json={"relative_path": "manual.md"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_validate_endpoint_dry_runs_without_embedding_key(tmp_path: Path) -> None:
    (tmp_path / "manual.md").write_text("# Demo\n\nInspect BIN-01 and preserve the result.", encoding="utf-8")
    app.dependency_overrides[get_settings] = lambda: settings(tmp_path)
    try:
        response = TestClient(app).post("/api/documents/validate", json={"relative_path": "manual.md"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["chunks_embedded"] == 0


def test_traversal_is_rejected(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings] = lambda: settings(tmp_path)
    try:
        response = TestClient(app).post("/api/documents/validate", json={"relative_path": "../secret.md"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422
