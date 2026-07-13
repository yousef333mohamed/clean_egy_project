"""Production-safe error response helpers."""

from fastapi import Request
from fastapi.responses import JSONResponse


async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
    return JSONResponse({"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)}, status_code=500)
