"""Decision endpoint."""

from typing import Annotated
from fastapi import APIRouter, Depends
from app.api.dependencies import get_decision
from app.schemas.decision import DecisionRequest, DecisionResponse
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("/recommend", response_model=DecisionResponse)
async def recommend(request: DecisionRequest, service: Annotated[DecisionService, Depends(get_decision)]) -> DecisionResponse:
    """Return an evidence-grounded operational recommendation."""
    return await service.recommend(request.question)
