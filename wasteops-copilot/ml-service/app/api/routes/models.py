from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import model_registry, require_admin_identity, require_service_identity

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/active", dependencies=[Depends(require_service_identity)])
def active(registry=Depends(model_registry)):
    return [
        {
            "model_name": m.model_name,
            "version": m.version,
            "stage": m.stage,
            "feature_version": m.feature_version,
            "approval_status": m.approval_status,
            "metrics": m.metrics,
            "training_period": {"start": m.training_period_start, "end": m.training_period_end},
        }
        for m in registry.active()
    ]


@router.get("/{model_name}", dependencies=[Depends(require_admin_identity)])
def details(model_name: str, registry=Depends(model_registry)):
    try:
        versions = registry.describe(model_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown model") from exc
    return [
        {
            "model_name": m.model_name,
            "version": m.version,
            "stage": m.stage,
            "feature_version": m.feature_version,
            "approval_status": m.approval_status,
            "metrics": m.metrics,
            "training_period": {"start": m.training_period_start, "end": m.training_period_end},
            "created_at": m.created_at,
            "promoted_at": m.promoted_at,
            "promoted_by": m.promoted_by,
        }
        for m in versions
    ]
