"""RAG chat API enablement and typed response tests."""

import uuid

from fastapi.testclient import TestClient

from app.api.routes import chat as route
from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.chat import RAGResponse
from app.services.llm_service import LLMError


def settings(*, enabled=True):
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        llm_api_key="fake",
        enable_chat_api=enabled,
    )


def test_disabled_chat_api() -> None:
    app.dependency_overrides[get_settings] = lambda: settings(enabled=False)
    try:
        response = TestClient(app).post("/api/chat/rag", json={"question": "sensor"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_grounded_chat_schema(monkeypatch) -> None:
    expected = RAGResponse(
        answer="Not enough context.",
        grounded=False,
        insufficient_context=True,
        citations=[],
        retrieved_evidence_count=0,
        used_evidence_count=0,
        warnings=[],
        query="unknown",
        rewritten_query=None,
        filters_applied={},
        request_id=uuid.uuid4(),
    )

    class Service:
        async def answer(self, _request):
            return expected

    monkeypatch.setattr(route, "build_rag_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = settings
    try:
        response = TestClient(app).post("/api/chat/rag", json={"question": "unknown"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["insufficient_context"] is True
    assert "embedding" not in response.text


def test_chat_provider_failure_returns_503(monkeypatch) -> None:
    class Service:
        async def answer(self, _request):
            raise LLMError("offline")

    monkeypatch.setattr(route, "build_rag_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = settings
    try:
        response = TestClient(app).post("/api/chat/rag", json={"question": "sensor"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
