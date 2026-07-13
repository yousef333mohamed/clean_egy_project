"""Retrieval debug API enablement, content restrictions, and schema safety."""

from fastapi.testclient import TestClient

from app.api.routes import retrieval as route
from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.retrieval import RetrievedEvidence, RetrievalResponse
from app.services.embedding_service import EmbeddingError


def settings(*, enabled=True, environment="development"):
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        llm_api_key="fake",
        enable_retrieval_debug_api=enabled,
        app_environment=environment,
    )


def test_disabled_and_invalid_filter_requests() -> None:
    app.dependency_overrides[get_settings] = lambda: settings(enabled=False)
    try:
        assert TestClient(app).post("/api/retrieval/search", json={"query": "sensor"}).status_code == 403
    finally:
        app.dependency_overrides.clear()
    app.dependency_overrides[get_settings] = settings
    try:
        response = TestClient(app).post("/api/retrieval/search", json={"query": "sensor", "filters": {"unknown": "x"}})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_production_response_omits_content_and_embeddings(monkeypatch) -> None:
    evidence = RetrievedEvidence(
        chunk_id="1",
        document_id="doc-1",
        source_filename="sensor.md",
        document_title="Sensor SOP",
        language="en",
        chunk_number=0,
        content="Sensor procedure",
        content_preview="Sensor procedure",
        final_score=0.8,
    )

    class Service:
        async def search(self, _request):
            return RetrievalResponse(
                query="sensor",
                rewritten_query=None,
                language="en",
                evidence=[evidence],
                filters_applied={},
            )

    monkeypatch.setattr(route, "build_retrieval_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = lambda: settings(environment="staging")
    try:
        response = TestClient(app).post(
            "/api/retrieval/search",
            json={"query": "sensor", "include_content": True},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    evidence = response.json()["evidence"][0]
    assert evidence["content"] is None
    assert "embedding" not in evidence
    assert "content_hash" not in evidence


def test_embedding_provider_failure_returns_503(monkeypatch) -> None:
    class Service:
        async def search(self, _request):
            raise EmbeddingError("offline")

    monkeypatch.setattr(route, "build_retrieval_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = settings
    try:
        response = TestClient(app).post("/api/retrieval/search", json={"query": "sensor"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
