"""Typed retrying HTTP client that propagates request IDs."""

import asyncio
import time
from collections.abc import Mapping
from typing import TypeVar, cast

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.integrations.data_science.circuit_breaker import CircuitBreaker
from app.integrations.data_science.errors import DataScienceUnavailable, InvalidPredictionRequest, InvalidPredictionResponse
from app.observability.prometheus import (
    ML_MODEL_UNAVAILABLE,
    ML_MODEL_VERSION_USAGE,
    ML_PREDICTION_FAILURES,
    ML_PREDICTION_LATENCY,
    ML_PREDICTION_REQUESTS,
    ML_PREDICTION_WARNINGS,
)

T = TypeVar("T", bound=BaseModel)


class DataScienceClient:
    def __init__(self, settings, *, transport: httpx.AsyncBaseTransport | None = None, token: str | None = None) -> None:
        self.max_retries = settings.ml_client_max_retries
        self.breaker = CircuitBreaker(settings.ml_circuit_breaker_failure_threshold, settings.ml_circuit_breaker_recovery_seconds)
        self.client = httpx.AsyncClient(
            base_url=settings.ml_service_base_url.rstrip("/"),
            timeout=settings.ml_client_timeout_seconds,
            transport=transport,
            headers={"Authorization": f"Bearer {token or settings.ml_service_token}"},
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def post(self, path: str, payload: Mapping[str, object], response_type: type[T], *, request_id: str) -> list[T]:
        metric_model = path.rsplit("/", 1)[-1]
        started = time.perf_counter()
        ML_PREDICTION_REQUESTS.labels(model=metric_model).inc()
        await self.breaker.before_call()
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(path, json=dict(payload), headers={"X-Request-ID": request_id})
                if response.status_code in {400, 404, 409, 422}:
                    await self.breaker.record_success()
                    raise InvalidPredictionRequest("ML service rejected the prediction request")
                response.raise_for_status()
                body = response.json()
                if body.get("request_id") != request_id:
                    raise InvalidPredictionResponse("ML response request ID mismatch")
                parsed = cast(list[T], TypeAdapter(list[response_type]).validate_python(body.get("predictions")))  # type: ignore[valid-type]
                for prediction in parsed:
                    ML_MODEL_VERSION_USAGE.labels(model=metric_model, version=str(getattr(prediction, "model_version", "unknown"))[:40]).inc()
                    for warning in getattr(prediction, "warnings", []):
                        category = "stale" if "stale" in warning.casefold() else "fallback" if "baseline" in warning.casefold() else "other"
                        ML_PREDICTION_WARNINGS.labels(model=metric_model, category=category).inc()
                await self.breaker.record_success()
                ML_PREDICTION_LATENCY.labels(model=metric_model).observe(time.perf_counter() - started)
                return parsed
            except InvalidPredictionRequest:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise InvalidPredictionRequest("ML service rejected the prediction request") from exc
                if attempt < self.max_retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                await self.breaker.record_failure()
                ML_PREDICTION_FAILURES.labels(model=metric_model, reason="unavailable").inc()
                ML_MODEL_UNAVAILABLE.labels(model=metric_model).inc()
                raise DataScienceUnavailable("Predictive models are unavailable") from exc
            except (ValidationError, ValueError, TypeError) as exc:
                await self.breaker.record_failure()
                ML_PREDICTION_FAILURES.labels(model=metric_model, reason="invalid_response").inc()
                raise InvalidPredictionResponse("ML service returned an invalid response") from exc
        raise DataScienceUnavailable("Predictive models are unavailable")

    async def get(self, path: str, response_type, *, request_id: str):
        await self.breaker.before_call()
        try:
            response = await self.client.get(path, headers={"X-Request-ID": request_id})
            if response.status_code == 404:
                raise InvalidPredictionRequest("Requested ML resource was not found")
            response.raise_for_status()
            parsed = TypeAdapter(response_type).validate_python(response.json())
            await self.breaker.record_success()
            return parsed
        except InvalidPredictionRequest:
            raise
        except (httpx.HTTPError, ValidationError, ValueError, TypeError) as exc:
            await self.breaker.record_failure()
            raise DataScienceUnavailable("ML model management is unavailable") from exc
