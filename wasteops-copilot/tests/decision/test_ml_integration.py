"""ML provider, circuit-breaker, evidence, and safety integration tests."""

from datetime import UTC, datetime

import httpx
import pytest

from app.decision.evidence_collector import DecisionEvidenceCollector
from app.decision.enums import DecisionEvidenceType, DecisionType
from app.integrations.data_science.circuit_breaker import CircuitBreaker, CircuitState
from app.integrations.data_science.client import DataScienceClient
from app.integrations.data_science.errors import CircuitBreakerOpen, DataScienceUnavailable, InvalidPredictionRequest
from app.integrations.data_science.schemas import BinOverflowPrediction
from app.schemas.decision import DecisionRequest, DecisionScope
from app.schemas.decision_context import DecisionContextPlan


def overflow_prediction() -> BinOverflowPrediction:
    timestamp = datetime.now(UTC)
    return BinOverflowPrediction(
        bin_id="BIN-1",
        horizon_hours=24,
        overflow_probability=0.87,
        predicted_class=True,
        decision_threshold=0.65,
        risk_level="HIGH",
        model_name="bin-overflow",
        model_version="3",
        prediction_timestamp=timestamp,
        feature_timestamp=timestamp,
        data_age_seconds=0,
        top_factors=[{"feature": "current_fill_level_pct", "direction": "increases_risk", "contribution": 0.3}],
    )


class Provider:
    async def predict_overflow(self, *_args, **_kwargs):
        return [overflow_prediction()]

    async def calculate_priority(self, *_args, **_kwargs):
        return []


class UnavailableProvider(Provider):
    async def predict_overflow(self, *_args, **_kwargs):
        raise DataScienceUnavailable("offline")


class Unused:
    async def execute(self, *_args):
        raise AssertionError("No analytics call was planned")

    async def search(self, *_args):
        raise AssertionError("No retrieval call was planned")


def predictive_plan() -> DecisionContextPlan:
    return DecisionContextPlan(
        decision_type=DecisionType.BIN_ATTENTION_PRIORITY,
        analytics_calls=[],
        document_queries=[],
        required_evidence_categories=["model_prediction"],
        requires_data_science=True,
    )


async def test_model_evidence_has_m_namespace_and_complete_lineage(decision_settings):
    collector = DecisionEvidenceCollector(Unused(), Unused(), object(), object(), decision_settings, data_science_provider=Provider())
    result = await collector.collect(
        DecisionRequest(question="Will BIN-1 overflow in 24 hours?", scope=DecisionScope(bin_ids=["BIN-1"])),
        predictive_plan(),
        request_id="request-1",
    )
    model = next(item for item in result.evidence if item.source_type == DecisionEvidenceType.MODEL)
    assert model.evidence_id == "M1"
    assert model.supporting_values["prediction_value"] == 0.87
    assert model.supporting_values["model_version"] == "3"
    assert "not policy" in " ".join(model.completeness_notes)


async def test_provider_outage_never_creates_fake_model_evidence(decision_settings):
    collector = DecisionEvidenceCollector(Unused(), Unused(), object(), object(), decision_settings, data_science_provider=UnavailableProvider())
    result = await collector.collect(DecisionRequest(question="Will BIN-1 overflow?", scope=DecisionScope(bin_ids=["BIN-1"])), predictive_plan())
    assert not any(item.source_type == DecisionEvidenceType.MODEL for item in result.evidence)
    assert any("no mock prediction" in warning for warning in result.warnings)


async def test_circuit_breaker_closed_open_half_open():
    clock = [0.0]
    breaker = CircuitBreaker(2, 10, clock=lambda: clock[0])
    await breaker.before_call()
    await breaker.record_failure()
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpen):
        await breaker.before_call()
    clock[0] = 11
    await breaker.before_call()
    assert breaker.state == CircuitState.HALF_OPEN
    await breaker.record_success()
    assert breaker.state == CircuitState.CLOSED


async def test_client_propagates_request_id_and_validates_response(decision_settings):
    async def handler(request: httpx.Request):
        assert request.headers["x-request-id"] == "request-1"
        prediction = overflow_prediction().model_dump(mode="json")
        return httpx.Response(200, json={"request_id": "request-1", "predictions": [prediction]})

    settings = decision_settings.model_copy(update={"ml_service_base_url": "http://ml", "ml_service_token": "secret", "ml_client_max_retries": 0})
    client = DataScienceClient(settings, transport=httpx.MockTransport(handler))
    result = await client.post("/api/predictions/bin-overflow", {}, BinOverflowPrediction, request_id="request-1")
    await client.close()
    assert result[0].model_version == "3"


async def test_client_does_not_retry_invalid_request(decision_settings):
    calls = 0

    async def handler(_request: httpx.Request):
        nonlocal calls
        calls += 1
        return httpx.Response(422, json={"detail": "invalid"})

    settings = decision_settings.model_copy(update={"ml_service_base_url": "http://ml", "ml_service_token": "secret", "ml_client_max_retries": 2})
    client = DataScienceClient(settings, transport=httpx.MockTransport(handler))
    with pytest.raises(InvalidPredictionRequest):
        await client.post("/api/predictions/bin-overflow", {}, BinOverflowPrediction, request_id="request-1")
    await client.close()
    assert calls == 1
