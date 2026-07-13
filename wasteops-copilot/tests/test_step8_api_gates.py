"""Administrative Step 8 APIs honor independent feature gates."""

from fastapi.testclient import TestClient
from datetime import UTC, datetime
import uuid

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.main import app


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://x:x@db/x", "database_sync_url": "postgresql+psycopg://x:x@db/x"}
    values.update(updates)
    return Settings(**values)


def test_administrative_apis_can_be_disabled_without_data_exposure():
    app.dependency_overrides[get_settings] = lambda: settings(
        enable_evaluation_api=False, enable_prompt_admin_api=False, enable_trace_api=False, enable_feedback_api=False
    )
    client = TestClient(app)
    try:
        responses = [
            client.get("/api/evaluation/datasets"),
            client.get("/api/prompts"),
            client.get("/api/traces/request-1"),
            client.post("/api/feedback", json={"rating": 5, "feedback_type": "HELPFUL"}),
        ]
    finally:
        app.dependency_overrides.clear()
    assert all(response.status_code == 403 for response in responses)
    assert all(term not in " ".join(response.text for response in responses).casefold() for term in ("password", "embedding", "select *", "system prompt"))


def test_feedback_submission_returns_no_private_comment():
    class Session:
        def add(self, record):
            self.record = record

        async def commit(self):
            pass

        async def refresh(self, record):
            record.id = uuid.uuid4()
            record.created_at = datetime.now(UTC)

    session = Session()

    async def database_override():
        yield session

    app.dependency_overrides[get_settings] = lambda: settings(enable_feedback_api=True)
    app.dependency_overrides[get_db_session] = database_override
    try:
        response = TestClient(app).post(
            "/api/feedback",
            json={"request_id": str(uuid.uuid4()), "rating": 2, "feedback_type": "INCORRECT_DATA", "comment": "<script>alert(1)</script> incorrect value"},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 201
    assert "comment" not in response.json() and "script" not in response.text.casefold()
    assert session.record.comment == "alert(1) incorrect value"
