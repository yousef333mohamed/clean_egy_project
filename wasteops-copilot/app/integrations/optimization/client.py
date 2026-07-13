import time

import httpx
from pydantic import ValidationError
from app.integrations.optimization.schemas import OptimizePayload, OptimizeResponse
from app.observability.prometheus import (
    OPTIMIZATION_FAILURES,
    OPTIMIZATION_LATENCY,
    OPTIMIZATION_REQUESTS,
    OPTIMIZATION_RESULTS,
    OPTIMIZATION_UNASSIGNED_BINS,
)


class OptimizationUnavailable(RuntimeError):
    pass


class OptimizationClient:
    def __init__(self, settings, transport=None):
        self.base_url = settings.optimization_service_base_url
        self.timeout = settings.optimization_timeout_seconds
        self.transport = transport
        self.token = settings.optimization_service_token

    async def optimize(self, payload: OptimizePayload, request_id: str) -> OptimizeResponse:
        OPTIMIZATION_REQUESTS.inc()
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                transport=self.transport,
                headers={"Authorization": f"Bearer {self.token}"},
            ) as client:
                response = await client.post(
                    "/api/plans/optimize",
                    json=payload.model_dump(mode="json"),
                    headers={"X-Request-ID": request_id},
                )
            response.raise_for_status()
            result = OptimizeResponse.model_validate(response.json())
            OPTIMIZATION_RESULTS.labels(status=result.status).inc()
            if result.primary_plan:
                OPTIMIZATION_UNASSIGNED_BINS.inc(len(result.primary_plan.unassigned_bin_ids))
            return result
        except (httpx.HTTPError, ValidationError) as exc:
            OPTIMIZATION_FAILURES.labels(reason=type(exc).__name__).inc()
            raise OptimizationUnavailable("Route optimizer unavailable") from exc
        finally:
            OPTIMIZATION_LATENCY.observe(time.perf_counter() - started)
