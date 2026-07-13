import hmac
from fastapi import APIRouter, Depends, Header, HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.config import get_settings
from app.engine.solver import optimize
from app.schemas.plans import OptimizeRequest, OptimizeResponse

router = APIRouter()


def authenticate(authorization: str | None = Header(default=None)):
    expected = f"Bearer {get_settings().service_token}"
    if not get_settings().service_token or not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=403, detail="Invalid service identity")


@router.get("/health/live")
def live():
    return {"status": "live"}


@router.get("/health/ready")
def ready():
    return {"status": "ready", "solver": "Google OR-Tools"}


@router.post("/plans/optimize", response_model=OptimizeResponse, dependencies=[Depends(authenticate)])
async def create_plan(body: OptimizeRequest):
    settings = get_settings()
    if len(body.bins) > settings.max_bins or len(body.trucks) > settings.max_trucks:
        raise HTTPException(status_code=422, detail="Optimization batch limit exceeded")
    return await run_in_threadpool(optimize, body, settings.solve_timeout_seconds, settings.max_alternative_plans)
