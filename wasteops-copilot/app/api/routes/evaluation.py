"""Feature-gated offline evaluation and release-gate APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.evaluation.evaluation_service import EvaluationService
from app.evaluation.quality_gate import QualityGate
from app.schemas.evaluation import CompareRunsRequest, StartEvaluationRequest

router = APIRouter(prefix="/evaluation", tags=["evaluation"])
AppSettings = Annotated[Settings, Depends(get_settings)]


def _enabled(settings: Settings) -> None:
    if not settings.enable_evaluation_api:
        raise HTTPException(status_code=403, detail="Evaluation API is disabled")


def _run_summary(run) -> dict:
    return {"id": str(run.id), "name": run.name, "evaluation_type": run.evaluation_type, "status": run.status,
        "dataset_name": run.dataset_name, "dataset_version": run.dataset_version, "started_at": run.started_at, "completed_at": run.completed_at,
        "total_cases": run.total_cases, "passed_cases": run.passed_cases, "failed_cases": run.failed_cases,
        "critical_failures": run.critical_failures, "metrics": run.metrics_json, "prompt_versions": run.prompt_versions_json}


@router.get("/datasets")
async def list_datasets(session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    return EvaluationService(session, settings).datasets()


@router.post("/runs", status_code=201)
async def start_run(request: StartEvaluationRequest, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    try:
        result = await EvaluationService(session, settings).start(request.dataset, request.mode, request.prompt_overrides)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"run_id": str(result.run_id), "status": "COMPLETED", "metrics": result.metrics, "critical_failures": result.critical_failures}


@router.get("/runs/{run_id}")
async def read_run(run_id: UUID, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    run = await EvaluationService(session, settings).get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return _run_summary(run)


@router.get("/runs/{run_id}/results")
async def list_results(run_id: UUID, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    results = await EvaluationService(session, settings).get_results(run_id)
    return [{"case_id": item.case_id, "category": item.category, "status": item.status, "metrics": item.metrics_json,
        "warnings": item.warnings_json, "failure_reasons": item.failure_reasons_json, "duration_ms": item.duration_ms} for item in results]


@router.get("/runs/{run_id}/quality-gate")
async def quality_gate(run_id: UUID, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    run = await EvaluationService(session, settings).get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return QualityGate(settings).evaluate(run.metrics_json, total_cases=run.total_cases, critical_failures=run.critical_failures)


@router.post("/compare")
async def compare_runs(request: CompareRunsRequest, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    try:
        return await EvaluationService(session, settings).compare(request.baseline, request.candidate)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
