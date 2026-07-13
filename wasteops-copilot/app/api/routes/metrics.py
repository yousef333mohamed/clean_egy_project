"""Internal metrics endpoint protected with a dedicated bearer secret."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.observability.prometheus import metrics_response

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/metrics", include_in_schema=False)
async def metrics(authorization: Annotated[str | None, Header()] = None, settings: Settings = Depends(get_settings)) -> Response:
    expected = f"Bearer {settings.metrics_token}"
    if not settings.metrics_token or not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    body, media_type = metrics_response()
    return Response(body, media_type=media_type)
