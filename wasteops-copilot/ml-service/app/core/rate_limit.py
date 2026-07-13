"""Small private-service fixed-window limiter; ingress should add distributed limits."""

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.limit = requests_per_minute
        self._counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self._lock = Lock()

    async def dispatch(self, request, call_next):
        if "/predictions/" not in request.url.path:
            return await call_next(request)
        key = request.headers.get("authorization", "")[-16:]
        window = int(time.time() // 60)
        with self._lock:
            state = self._counts[key]
            if state[0] != window:
                state[:] = [window, 0]
            state[1] += 1
            allowed = state[1] <= self.limit
        if not allowed:
            return JSONResponse({"detail": "Prediction rate limit exceeded"}, status_code=429)
        return await call_next(request)
