"""Concurrency-safe CLOSED/OPEN/HALF_OPEN circuit breaker."""

import asyncio
import time
from enum import StrEnum

from app.integrations.data_science.errors import CircuitBreakerOpen


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_seconds: float, *, clock=time.monotonic) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.clock = clock
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.opened_at: float | None = None
        self._probe_in_flight = False
        self._lock = asyncio.Lock()

    async def before_call(self) -> None:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self.opened_at is None or self.clock() - self.opened_at < self.recovery_seconds:
                    raise CircuitBreakerOpen("ML provider circuit is open")
                self.state = CircuitState.HALF_OPEN
            if self.state == CircuitState.HALF_OPEN:
                if self._probe_in_flight:
                    raise CircuitBreakerOpen("ML provider recovery probe is already running")
                self._probe_in_flight = True

    async def record_success(self) -> None:
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.opened_at = None
            self._probe_in_flight = False

    async def record_failure(self) -> None:
        async with self._lock:
            self.failures += 1
            self._probe_in_flight = False
            if self.state == CircuitState.HALF_OPEN or self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = self.clock()
