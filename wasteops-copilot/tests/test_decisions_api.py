"""Decision catalog, preview, recommendation, debug, and exposure tests."""

import uuid

from fastapi.testclient import TestClient

from app.api.routes import decisions as route
from app.core.config import Settings, get_settings
from app.decision.enums import ConfidenceLevel, DecisionType
from app.main import app
from app.schemas.confidence import ConfidenceComponents, DecisionConfidence
from app.schemas.decision import DecisionDebugResponse, DecisionResponse
from app.schemas.decision_context import DecisionRouteResult
from app.services.llm_service import LLMError


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://test:test@db/test", "database_sync_url": "postgresql+psycopg://test:test@db/test", "llm_api_key": ""}
    values.update(updates)
    return Settings(**values)


def test_decision_type_catalog_is_safe():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).get("/api/decisions/types")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200 and len(response.json()) == 7
    assert all(term not in response.text.casefold() for term in ("sql", "embedding", "prompt", "password"))


def test_preview_does_not_execute_and_preserves_id():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/decisions/preview", json={"question": "Should TRK-014 be inspected?"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert all(call["parameters"]["truck_id"] == "TRK-014" for call in response.json()["plan"]["analytics_calls"])


def test_invalid_constraints_are_422():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/decisions/preview", json={"question": "bins", "constraints": {"disable_safety": True}})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_debug_can_be_disabled():
    app.dependency_overrides[get_settings] = lambda: settings(enable_decision_debug_api=False)
    try:
        response = TestClient(app).post("/api/decisions/debug", json={"question": "bins"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_enabled_debug_is_summary_only(monkeypatch):
    confidence = DecisionConfidence(
        score=0.5,
        level=ConfidenceLevel.MEDIUM,
        components=ConfidenceComponents(retrieval_coverage=0.5, source_quality=0.5, data_completeness=0.5, source_agreement=0.5, recency=0.5),
        explanation="quality",
    )
    expected = DecisionDebugResponse(
        request_id=uuid.uuid4(),
        router_output=DecisionRouteResult(decision_type=DecisionType.BIN_ATTENTION_PRIORITY),
        evidence_summary=[{"evidence_id": "D1", "source_type": "database", "has_data": True}],
        option_scores=[{"option_id": "O1", "score": 0.5}],
        confidence=confidence,
        insufficient_context=False,
    )

    class Service:
        async def debug(self, _request):
            return expected

    monkeypatch.setattr(route, "build_decision_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/decisions/debug", json={"question": "bins"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert all(term not in response.text.casefold() for term in ("sql", "prompt", "embedding", "credential"))


def test_predictive_decision_is_insufficient_without_provider():
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/decisions/recommend", json={"question": "Which bins will overflow tomorrow?"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["decision_type"] == "BIN_ATTENTION_PRIORITY"
    assert body["requires_human_approval"] is True and body["insufficient_context"] is True


def test_recommend_response_schema_and_no_internal_exposure(monkeypatch):
    confidence = DecisionConfidence(
        score=0,
        level=ConfidenceLevel.LOW,
        components=ConfidenceComponents(retrieval_coverage=0, source_quality=0, data_completeness=0, source_agreement=0, recency=0),
        explanation="evidence quality",
    )
    expected = DecisionResponse(
        request_id=uuid.uuid4(),
        decision_type=DecisionType.BIN_ATTENTION_PRIORITY,
        situation_summary="Insufficient evidence",
        recommended_option=None,
        alternative_options=[],
        database_evidence=[],
        document_citations=[],
        confidence=confidence,
        missing_information=["latest readings"],
        warnings=["human approval required"],
        requires_human_approval=True,
        grounded=False,
        insufficient_context=True,
    )

    class Service:
        async def recommend(self, _request):
            return expected

    monkeypatch.setattr(route, "build_decision_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/decisions/recommend", json={"question": "Which bins need attention?"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert all(term not in response.text.casefold() for term in ("embedding", "system prompt", "select *", "database_url"))


def test_provider_failure_is_503(monkeypatch):
    class Service:
        async def recommend(self, _request):
            raise LLMError("offline")

    monkeypatch.setattr(route, "build_decision_service", lambda *_args: Service())
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        response = TestClient(app).post("/api/decisions/recommend", json={"question": "bins"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "offline" not in response.text
