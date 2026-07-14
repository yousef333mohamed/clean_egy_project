"""Authorized backend facade for private ML model and monitoring summaries."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth.dependencies import require_any_permission
from app.core.config import Settings, get_settings
from app.integrations.data_science.errors import DataScienceError
from app.integrations.data_science.factory import build_ml_admin_client, build_ml_service_client
from app.integrations.data_science.factory import build_data_science_provider
from app.integrations.data_science.schemas import (
    ActiveModel,
    BinOverflowPrediction,
    CollectionPriorityPrediction,
    ModelVersion,
    MonitoringReportEnvelope,
    TruckAnomalyPrediction,
)
from app.utils.safe_identifiers import validate_safe_value

router = APIRouter(prefix="/ml", tags=["machine-learning"], dependencies=[Depends(require_any_permission("system:configure"))])
prediction_router = APIRouter(
    prefix="/ml/predictions",
    tags=["machine-learning"],
    dependencies=[Depends(require_any_permission("decisions:request"))],
)
AppSettings = Annotated[Settings, Depends(get_settings)]


class PromotionReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9.-]+$")
    target_stage: Literal["Staging", "Production"]
    reason: str = Field(min_length=20, max_length=500)


class AssetPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_ids: list[str] = Field(min_length=1, max_length=200)
    horizon_hours: Literal[6, 12, 24] = 24

    @field_validator("asset_ids")
    @classmethod
    def safe_asset_ids(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(validate_safe_value(value) for value in values))


def _client(settings: Settings):
    client = build_ml_admin_client(settings)
    if client is None:
        raise HTTPException(status_code=503, detail="ML model management is unavailable")
    return client


def _service_client(settings: Settings):
    client = build_ml_service_client(settings)
    if client is None:
        raise HTTPException(status_code=503, detail="ML model management is unavailable")
    return client


@router.get("/models/active", response_model=list[ActiveModel])
async def active_models(request: Request, settings: AppSettings):
    try:
        return await _service_client(settings).get("/api/models/active", list[ActiveModel], request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="ML model management is unavailable") from exc


@router.get("/models/{model_name}", response_model=list[ModelVersion])
async def model_versions(
    model_name: Literal["bin-overflow", "collection-priority", "truck-anomaly", "missed-collection", "workforce-forecast"],
    request: Request,
    settings: AppSettings,
):
    try:
        return await _client(settings).get(f"/api/models/{model_name}", list[ModelVersion], request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="ML model management is unavailable") from exc


@router.post("/models/{model_name}/promotion-requests", status_code=status.HTTP_202_ACCEPTED)
async def request_promotion_review(
    model_name: Literal["bin-overflow", "collection-priority", "truck-anomaly", "missed-collection", "workforce-forecast"],
    body: PromotionReviewRequest,
    request: Request,
    settings: AppSettings,
):
    try:
        versions = await _client(settings).get(f"/api/models/{model_name}", list[ModelVersion], request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="ML model management is unavailable") from exc
    if body.version not in {item.version for item in versions}:
        raise HTTPException(status_code=404, detail="Requested model version is not registered")
    return {
        "status": "REQUESTED",
        "model_name": model_name,
        "version": body.version,
        "target_stage": body.target_stage,
        "executes_promotion": False,
        "request_id": request.state.request_id,
    }


@router.get("/monitoring/{report_type}", response_model=MonitoringReportEnvelope)
async def monitoring(report_type: Literal["drift", "performance", "data-quality"], request: Request, settings: AppSettings):
    try:
        return await _client(settings).get(f"/api/monitoring/{report_type}", MonitoringReportEnvelope, request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="ML monitoring is unavailable") from exc


@prediction_router.post("/bin-overflow", response_model=list[BinOverflowPrediction])
async def predict_overflow(body: AssetPredictionRequest, request: Request, settings: AppSettings):
    try:
        predictions = await build_data_science_provider(settings).predict_overflow(body.asset_ids, body.horizon_hours, request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="Predictive models are unavailable") from exc
    if not predictions:
        raise HTTPException(status_code=503, detail="Predictive models are unavailable")
    return predictions


@prediction_router.post("/collection-priority", response_model=list[CollectionPriorityPrediction])
async def collection_priority(body: AssetPredictionRequest, request: Request, settings: AppSettings):
    try:
        predictions = await build_data_science_provider(settings).calculate_priority(body.asset_ids, body.horizon_hours, request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="Predictive models are unavailable") from exc
    if not predictions:
        raise HTTPException(status_code=503, detail="Predictive models are unavailable")
    return predictions


@prediction_router.post("/truck-anomalies", response_model=list[TruckAnomalyPrediction])
async def truck_anomalies(body: AssetPredictionRequest, request: Request, settings: AppSettings):
    try:
        predictions = await build_data_science_provider(settings).detect_anomalies(body.asset_ids, request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="Predictive models are unavailable") from exc
    if not predictions:
        raise HTTPException(status_code=503, detail="Predictive models are unavailable")
    return predictions
