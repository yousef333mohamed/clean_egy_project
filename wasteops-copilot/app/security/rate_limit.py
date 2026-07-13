"""Redis-backed fixed-window rate limiting with bounded local degradation."""

import asyncio
import hashlib
import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply distributed limits; local fallback is a degraded safety net."""

    def __init__(self, app, settings) -> None:
        super().__init__(app)
        self.settings = settings
        self._local: dict[tuple[str, int], int] = defaultdict(int)
        self._lock = asyncio.Lock()
        self._redis: Any = None

    def _limit(self, path: str) -> int:
        if any(part in path for part in ("/evaluation", "/ingestion", "/documents/ingest", "/chat/")):
            return self.settings.rate_limit_expensive_per_minute
        if any(part in path for part in ("/prompts", "/audit")):
            return self.settings.rate_limit_admin_per_minute
        return self.settings.rate_limit_default_per_minute

    @staticmethod
    def _identity(request) -> str:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            return "token:" + hashlib.sha256(authorization[7:].encode()).hexdigest()
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        return "ip:" + (forwarded or (request.client.host if request.client else "unknown"))

    async def _count(self, key: str, window: int) -> int:
        try:
            if self._redis is None:
                from redis.asyncio import from_url

                self._redis = from_url(self.settings.redis_url, socket_connect_timeout=0.2, socket_timeout=0.2, decode_responses=True)
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, 65)
            return int(count)
        except Exception:
            if self.settings.redis_required:
                raise
            async with self._lock:
                local_key = (key, window)
                self._local[local_key] += 1
                if len(self._local) > 10_000:
                    self._local = defaultdict(int, {k: v for k, v in self._local.items() if k[1] >= window - 1})
                return self._local[local_key]

    async def dispatch(self, request, call_next):
        if not self.settings.rate_limit_enabled or request.method == "OPTIONS" or request.url.path.startswith("/api/health"):
            return await call_next(request)
        window = int(time.time() // 60)
        identity = hashlib.sha256(self._identity(request).encode()).hexdigest()
        key = f"{self.settings.rate_limit_key_prefix}:{identity}:{window}"
        limit = self._limit(request.url.path)
        try:
            count = await self._count(key, window)
        except Exception:
            return JSONResponse({"detail": "Rate-limit service unavailable"}, status_code=503)
        if count > limit:
            from app.observability.prometheus import RATE_LIMITS

            RATE_LIMITS.inc()
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429, headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)})
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
