from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import model_registry, prediction_service, require_service_identity
from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live():
    return {"status": "live"}


@router.get("/ready")
def ready(registry=Depends(model_registry)):
    settings = get_settings()
    active = registry.active()
    if settings.require_production_models and len(active) < 5:
        raise HTTPException(status_code=503, detail="Required production models are unavailable")
    try:
        prediction_service()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Approved production models failed validation") from exc
    return {"status": "ready", "production_model_count": len(active), "baseline_fallback_enabled": not settings.require_production_models}


@router.get("/models", dependencies=[Depends(require_service_identity)])
def model_health(registry=Depends(model_registry)):
    return {item.model_name: {"available": True, "version": item.version, "stage": item.stage} for item in registry.active()}
