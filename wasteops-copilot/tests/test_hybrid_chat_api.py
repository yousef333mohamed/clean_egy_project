"""Hybrid endpoint enablement and typed response."""

import uuid

from fastapi.testclient import TestClient

from app.analytics.enums import AnalyticsRoute
from app.api.routes import chat as route
from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.hybrid_answer import HybridQuestionResponse


def settings(enabled=True):
    return Settings(
        database_url="postgresql+asyncpg://test:test@db/test",
        database_sync_url="postgresql+psycopg://test:test@db/test",
        llm_api_key="fake",
        enable_hybrid_chat_api=enabled,
    )


def test_hybrid_chat_disabled():
    app.dependency_overrides[get_settings] = lambda: settings(False)
    try:
        response = TestClient(app).post("/api/chat/hybrid", json={"question": "missed collections and procedure"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_hybrid_chat_schema(monkeypatch):
    expected = HybridQuestionResponse(
        answer="Unsupported",
        route=AnalyticsRoute.UNSUPPORTED,
        grounded=False,
        insufficient_data=True,
        insufficient_context=True,
        database_evidence=[],
        document_citations=[],
        warnings=["prediction"],
        request_id=uuid.uuid4(),
    )

    class Service:
        async def answer(self, _request):
            return expected

    monkeypatch.setattr(route, "build_hybrid_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = settings
    try:
        response = TestClient(app).post("/api/chat/hybrid", json={"question": "predict"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200 and response.json()["route"] == "UNSUPPORTED"
