import json
from pathlib import Path
from fastapi import APIRouter, Depends
from app.api.dependencies import model_registry, require_admin_identity

router = APIRouter(prefix="/monitoring", tags=["monitoring"], dependencies=[Depends(require_admin_identity)])


def _reports(kind: str) -> list[dict]:
    root = Path("artifacts/reports") / kind
    result = []
    for path in sorted(root.glob("*.json"), reverse=True)[:100]:
        try:
            result.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return result


@router.get("/models")
def models(registry=Depends(model_registry)):
    return [{"model_name": m.model_name, "version": m.version, "stage": m.stage, "approval_status": m.approval_status} for m in registry.active()]


@router.get("/drift")
def drift():
    return {"reports": _reports("drift"), "interpretation": "Drift signals require review and are not definitive proof of failure."}


@router.get("/performance")
def performance():
    return {"reports": _reports("performance"), "outcome_labels_required": True}


@router.get("/data-quality")
def quality():
    return {"reports": _reports("data-quality")}
