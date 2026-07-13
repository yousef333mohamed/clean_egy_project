"""Incident endpoint."""

from typing import Annotated
from fastapi import APIRouter, Depends
from app.api.dependencies import get_incident
from app.schemas.incident import IncidentRequest, IncidentResponse
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("/investigate", response_model=IncidentResponse)
async def investigate(request: IncidentRequest, service: Annotated[IncidentService, Depends(get_incident)]) -> IncidentResponse:
    """Investigate an operational incident from structured and document evidence."""
    return await service.investigate(request.question)
