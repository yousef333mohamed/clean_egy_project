"""Recommendation-only Decision Intelligence APIs; no operational mutations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.analytics.query_executor import AnalyticsDatabaseError
from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.decision.factory import build_decision_preview, build_decision_service
from app.schemas.decision import DecisionDebugResponse, DecisionPreviewResponse, DecisionRequest, DecisionResponse
from app.services.embedding_service import EmbeddingError
from app.services.llm_service import LLMError

router = APIRouter(prefix="/decisions", tags=["decisions"])
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.get("/types")
async def decision_types(settings: AppSettings) -> list[dict[str, object]]:
    if not settings.enable_decision_api:
        raise HTTPException(status_code=403, detail="Decision API is disabled")
    return build_decision_preview(settings)[0].catalog()


@router.post("/preview", response_model=DecisionPreviewResponse)
async def preview_decision(request: DecisionRequest, settings: AppSettings) -> DecisionPreviewResponse:
    if not settings.enable_decision_api:
        raise HTTPException(status_code=403, detail="Decision API is disabled")
    _registry, _analytics, router_service, planner, _llm = build_decision_preview(settings)
    route = await router_service.route(request)
    return DecisionPreviewResponse(route=route, plan=planner.plan(request, route))


@router.post("/recommend", response_model=DecisionResponse)
async def recommend_decision(request: DecisionRequest, session: DatabaseSession, settings: AppSettings) -> DecisionResponse:
    if not settings.enable_decision_api:
        raise HTTPException(status_code=403, detail="Decision API is disabled")
    try:
        return await build_decision_service(session, settings).recommend(request)
    except (AnalyticsDatabaseError, EmbeddingError, LLMError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Decision evidence provider unavailable") from exc


@router.post("/debug", response_model=DecisionDebugResponse)
async def debug_decision(request: DecisionRequest, session: DatabaseSession, settings: AppSettings) -> DecisionDebugResponse:
    if not settings.enable_decision_debug_api:
        raise HTTPException(status_code=403, detail="Decision debug API is disabled")
    try:
        return await build_decision_service(session, settings).debug(request)
    except (AnalyticsDatabaseError, EmbeddingError, LLMError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Decision evidence provider unavailable") from exc
