"""Safe development tools and natural-language operational analytics APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.analytics.analytics_service import AnalyticsService
from app.analytics.enums import AnalyticsRoute
from app.analytics.factory import build_analytics_stack
from app.analytics.parameter_parser import AnalyticsParameterError
from app.analytics.query_executor import AnalyticsDatabaseError
from app.analytics.tool_registry import UnknownAnalyticsTool, build_tool_registry
from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.schemas.analytics import AnalyticsQueryRequest, AnalyticsResponse, AnalyticsRouteDecision
from app.schemas.analytics_tools import AnalyticsToolRequest
from app.schemas.operational_evidence import OperationalEvidence
from app.services.llm_service import LLMError

router = APIRouter(prefix="/analytics", tags=["analytics"])
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.get("/tools")
async def list_tools(settings: AppSettings) -> list[dict[str, object]]:
    if not settings.enable_analytics_api:
        raise HTTPException(status_code=403, detail="Analytics API is disabled")
    return build_tool_registry(settings).catalog()


@router.post("/tools/{tool_name}", response_model=OperationalEvidence)
async def execute_tool(tool_name: str, request: AnalyticsToolRequest, session: DatabaseSession, settings: AppSettings) -> OperationalEvidence:
    if not settings.enable_analytics_api:
        raise HTTPException(status_code=403, detail="Analytics API is disabled")
    try:
        registry = build_tool_registry(settings)
        return await AnalyticsService(registry, settings).execute(tool_name, request.parameters, session)
    except UnknownAnalyticsTool as exc:
        raise HTTPException(status_code=404, detail="Unknown analytics tool") from exc
    except AnalyticsParameterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnalyticsDatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/query", response_model=AnalyticsResponse)
async def query_analytics(request: AnalyticsQueryRequest, session: DatabaseSession, settings: AppSettings) -> AnalyticsResponse:
    if not settings.enable_analytics_api:
        raise HTTPException(status_code=403, detail="Analytics API is disabled")
    try:
        _registry, route_service, analytics, answer_service, _llm = build_analytics_stack(session, settings)
        decision = await route_service.route(request.question)
        if decision.route != AnalyticsRoute.STRUCTURED_DATA:
            reason = decision.unsupported_reason or "This route requires the document-capable /api/chat/hybrid endpoint."
            return AnalyticsResponse(
                answer=reason,
                route=decision.route,
                grounded=False,
                insufficient_data=True,
                database_evidence=[],
                citations=[],
                warnings=[reason],
                request_id=__import__("uuid").uuid4(),
            )
        evidence = await analytics.execute(decision.tool_name, decision.parameters, session)
        response = await answer_service.answer(question=request.question, decision=decision, evidence=evidence)
        if not request.debug or not settings.analytics_enable_debug_api:
            response.debug = None
        return response
    except AnalyticsParameterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (AnalyticsDatabaseError, LLMError) as exc:
        raise HTTPException(status_code=503, detail="Analytics dependency unavailable") from exc


@router.post("/route", response_model=AnalyticsRouteDecision)
async def debug_route(request: AnalyticsQueryRequest, session: DatabaseSession, settings: AppSettings) -> AnalyticsRouteDecision:
    if not settings.analytics_enable_debug_api:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Analytics debug API is disabled")
    try:
        return await build_analytics_stack(session, settings)[1].route(request.question)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail="AI provider unavailable") from exc
