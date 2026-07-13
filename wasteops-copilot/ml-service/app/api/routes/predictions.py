"""Private prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import prediction_service, request_id, require_service_identity
from app.inference.prediction_validator import PredictionValidationError
from app.schemas.collection_priority import CollectionPriorityRequest, CollectionPriorityResponse
from app.schemas.missed_collection import MissedCollectionRequest, MissedCollectionResponse
from app.schemas.overflow import OverflowPredictionRequest, OverflowPredictionResponse
from app.schemas.truck_anomaly import TruckAnomalyRequest, TruckAnomalyResponse
from app.schemas.workforce_forecast import WorkforceForecastRequest, WorkforceForecastResponse

router = APIRouter(prefix="/predictions", tags=["predictions"], dependencies=[Depends(require_service_identity)])


async def _call(function, *args):
    try:
        return await run_in_threadpool(function, *args)
    except PredictionValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Prediction features or model are unavailable") from exc


@router.post("/bin-overflow", response_model=OverflowPredictionResponse)
async def overflow(body: OverflowPredictionRequest, rid: str = Depends(request_id), service=Depends(prediction_service)):
    return OverflowPredictionResponse(request_id=rid, predictions=await _call(service.overflow, body.bin_ids, body.horizon_hours, body.prediction_time()))


@router.post("/collection-priority", response_model=CollectionPriorityResponse)
async def priority(body: CollectionPriorityRequest, rid: str = Depends(request_id), service=Depends(prediction_service)):
    return CollectionPriorityResponse(request_id=rid, predictions=await _call(service.priority, body.bin_ids, body.horizon_hours, body.prediction_time()))


@router.post("/truck-anomalies", response_model=TruckAnomalyResponse)
async def trucks(body: TruckAnomalyRequest, rid: str = Depends(request_id), service=Depends(prediction_service)):
    return TruckAnomalyResponse(request_id=rid, predictions=await _call(service.truck_anomalies, body.truck_ids, body.prediction_time()))


@router.post("/missed-collections", response_model=MissedCollectionResponse)
async def missed(body: MissedCollectionRequest, rid: str = Depends(request_id), service=Depends(prediction_service)):
    return MissedCollectionResponse(
        request_id=rid, predictions=await _call(service.missed, body.scope_ids, body.scope_type, body.horizon_hours, body.prediction_time())
    )


@router.post("/workforce-requirements", response_model=WorkforceForecastResponse)
async def workforce(body: WorkforceForecastRequest, rid: str = Depends(request_id), service=Depends(prediction_service)):
    return WorkforceForecastResponse(
        request_id=rid, predictions=await _call(service.workforce, body.regions, body.shifts, body.forecast_date, body.prediction_time())
    )
