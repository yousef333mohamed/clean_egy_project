import json
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from app.api.dependencies import DatabaseSession
from app.auth.dependencies import require_permission
from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.integrations.data_science.errors import DataScienceError
from app.integrations.data_science.factory import build_data_science_provider
from app.integrations.optimization.client import OptimizationClient, OptimizationUnavailable
from app.integrations.optimization.schemas import (
    BinInput,
    Constraints,
    Location,
    OptimizePayload,
    OptimizeResponse,
    PlanExplanation,
    PlanPreviewRequest,
    PlanReviewRequest,
    TruckInput,
)
from app.models.optimization_plan import OptimizationPlan
from app.models.smart_bin import SmartBin
from app.models.smart_bin_reading import SmartBinReading
from app.models.truck import Truck
from app.models.truck_trip_log import TruckTripLog
from app.models.worker import Worker
from app.models.workforce_attendance import WorkforceAttendance
from app.observability.tracer import Tracer
from app.services.llm_service import LLMError, LLMService

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.post("/plans/preview", response_model=OptimizeResponse, dependencies=[Depends(require_permission("optimization:request"))])
async def preview(body: PlanPreviewRequest, request: Request, session: DatabaseSession, settings: Settings = Depends(get_settings)):
    if settings.optimization_provider != "remote":
        raise HTTPException(status_code=503, detail="Route optimization is unavailable")
    bins = list((await session.execute(select(SmartBin).where(SmartBin.bin_id.in_(body.bin_ids)))).scalars())
    trucks = list((await session.execute(select(Truck).where(Truck.truck_id.in_(body.truck_ids)))).scalars())
    if {x.bin_id for x in bins} != set(body.bin_ids) or {x.truck_id for x in trucks} != set(body.truck_ids):
        raise HTTPException(status_code=422, detail="Unknown bin or truck identifier")
    readings = list(
        (await session.execute(select(SmartBinReading).where(SmartBinReading.bin_id.in_(body.bin_ids)).order_by(SmartBinReading.timestamp.desc()))).scalars()
    )
    latest: dict[str, SmartBinReading] = {}
    for item in readings:
        latest.setdefault(item.bin_id, item)
    if set(latest) != set(body.bin_ids):
        raise HTTPException(status_code=422, detail="Missing current bin telemetry")
    if any(item.waste_weight_kg is None for item in latest.values()):
        raise HTTPException(status_code=422, detail="Current waste-weight telemetry is required for every bin")
    provider = build_data_science_provider(settings)
    try:
        overflow = await provider.predict_overflow(body.bin_ids, 24, request_id=request.state.request_id)
        priority = await provider.calculate_priority(body.bin_ids, 24, request_id=request.state.request_id)
    except DataScienceError as exc:
        raise HTTPException(status_code=503, detail="Required predictive scores are unavailable") from exc
    overflow_by = {x.bin_id: x for x in overflow}
    priority_by = {x.bin_id: x for x in priority}
    if set(overflow_by) != set(body.bin_ids) or set(priority_by) != set(body.bin_ids):
        raise HTTPException(status_code=503, detail="Complete predictive scores are unavailable")
    prediction_warnings = [warning for item in [*overflow, *priority] for warning in item.warnings]
    if any(item.is_synthetic for item in [*overflow, *priority]):
        raise HTTPException(status_code=422, detail="Synthetic predictions cannot support operational route planning")
    if any("stale" in warning.casefold() for warning in prediction_warnings):
        raise HTTPException(status_code=422, detail="Predictive evidence is stale; refresh features before planning")
    regions = {x.region for x in bins}
    latest_day = (
        await session.execute(
            select(func.max(WorkforceAttendance.date)).join(Worker).where(Worker.region.in_(regions), WorkforceAttendance.date <= body.plan_date)
        )
    ).scalar_one_or_none()
    workers = (
        0
        if latest_day is None
        else int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(WorkforceAttendance)
                    .join(Worker)
                    .where(Worker.region.in_(regions), WorkforceAttendance.date == latest_day, WorkforceAttendance.present.is_(True))
                )
            ).scalar_one()
        )
    )
    bin_inputs = []
    for asset in bins:
        reading = latest[asset.bin_id]
        if reading.waste_weight_kg is None:  # Defensive narrowing after the batch-level check.
            raise HTTPException(status_code=422, detail="Current waste-weight telemetry is required for every bin")
        op = overflow_by[asset.bin_id]
        pp = priority_by[asset.bin_id]
        bin_inputs.append(
            BinInput(
                bin_id=asset.bin_id,
                location=Location(latitude=float(asset.latitude), longitude=float(asset.longitude)),
                estimated_load_kg=round(float(reading.waste_weight_kg)),
                priority_score=pp.priority_score,
                overflow_probability=op.overflow_probability,
                feature_timestamp=min(op.feature_timestamp, pp.feature_timestamp),
                model_versions={"bin-overflow": op.model_version, "collection-priority": pp.model_version},
            )
        )
    trip_logs = list(
        (
            await session.execute(
                select(TruckTripLog).where(TruckTripLog.truck_id.in_(body.truck_ids), TruckTripLog.date <= body.plan_date).order_by(TruckTripLog.date.desc())
            )
        ).scalars()
    )
    latest_trip: dict[str, TruckTripLog] = {}
    for trip in trip_logs:
        latest_trip.setdefault(trip.truck_id, trip)
    unavailable_statuses = {"under maintenance", "out of service", "inactive"}
    payload = OptimizePayload(
        bins=bin_inputs,
        trucks=[
            TruckInput(
                truck_id=x.truck_id,
                capacity_kg=x.capacity_kg,
                depot=body.depot,
                available=(x.truck_id in latest_trip and latest_trip[x.truck_id].status.casefold() not in unavailable_statuses),
            )
            for x in trucks
        ],
        constraints=Constraints(
            plan_date=body.plan_date,
            available_workers=workers,
            workers_per_route=body.workers_per_route,
            average_speed_kmh=body.average_speed_kmh,
            traffic_multiplier=body.traffic_multiplier,
            environmental_duration_multiplier=body.environmental_duration_multiplier,
            working_day_minutes=480,
        ),
    )
    try:
        result = await OptimizationClient(settings).optimize(payload, request.state.request_id)
    except OptimizationUnavailable as exc:
        raise HTTPException(status_code=503, detail="Route optimization is unavailable") from exc
    operational_assumptions = list(result.assumptions)
    operational_assumptions.append(f"Workforce availability is based on attendance dated {latest_day.isoformat() if latest_day else 'unavailable'}.")
    trucks_without_status = sorted(set(body.truck_ids) - set(latest_trip))
    operational_warnings = [*result.warnings, *prediction_warnings]
    if trucks_without_status:
        operational_warnings.append("Trucks without a historical availability status were treated as unavailable: " + ", ".join(trucks_without_status))
    result = result.model_copy(update={"assumptions": operational_assumptions, "warnings": operational_warnings})
    session.add(
        OptimizationPlan(
            solver_plan_id=result.plan_id,
            request_id=request.state.request_id,
            plan_date=body.plan_date,
            status=result.status,
            request_json=payload.model_dump(mode="json"),
            result_json=result.model_dump(mode="json"),
        )
    )
    await session.flush()
    return result


@router.get("/plans/{plan_id}", response_model=OptimizeResponse, dependencies=[Depends(require_permission("optimization:request"))])
async def get_plan(plan_id: str, session: DatabaseSession):
    plan = (await session.execute(select(OptimizationPlan).where(OptimizationPlan.solver_plan_id == plan_id))).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return OptimizeResponse.model_validate(plan.result_json)


@router.post("/plans/{plan_id}/review", dependencies=[Depends(require_permission("optimization:approve"))])
async def review(plan_id: str, body: PlanReviewRequest, session: DatabaseSession):
    plan = (await session.execute(select(OptimizationPlan).where(OptimizationPlan.solver_plan_id == plan_id).with_for_update())).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.review_status != "PENDING":
        raise HTTPException(status_code=409, detail="Plan review has already been recorded")
    plan.review_status = "APPROVED" if body.approved else "REJECTED"
    plan.review_notes = body.review_notes
    plan.reviewed_at = datetime.now(UTC)
    await session.flush()
    return {
        "plan_id": plan_id,
        "review_status": plan.review_status,
        "executes_operations": False,
        "message": "Review recorded. No truck was dispatched and no worker was assigned.",
    }


def _deterministic_explanation(result: OptimizeResponse) -> str:
    if not result.primary_plan:
        return (
            "No feasible primary route satisfies the submitted capacity, time, truck, and workforce "
            "constraints. Review the listed alternatives and warnings before deciding [O1]."
        )
    summary = result.primary_plan
    return (
        f"The advisory plan contains {len(summary.routes)} routes covering "
        f"{sum(len(route.stops) for route in summary.routes)} stops, with "
        f"{len(summary.unassigned_bin_ids)} unassigned bins. Estimated totals are "
        f"{summary.total_distance_km} km, {summary.total_duration_minutes} minutes, "
        f"{summary.total_load_kg} kg, and {summary.total_fuel_liters} liters. "
        "Priority and overflow scores influence early service and dropped-stop penalties; the manager "
        "must review assumptions, warnings, and alternatives before approval [O1]."
    )


def _numbers_are_grounded(answer: str, evidence: str) -> bool:
    answer_without_citations = re.sub(r"\[O\d+\]", "", answer)
    answer_numbers = set(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", answer_without_citations))
    evidence_numbers = set(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", evidence))
    return answer_numbers <= evidence_numbers


@router.post(
    "/plans/{plan_id}/explain",
    response_model=PlanExplanation,
    dependencies=[Depends(require_permission("optimization:request"))],
)
async def explain(plan_id: str, session: DatabaseSession, settings: Settings = Depends(get_settings)):
    plan = (await session.execute(select(OptimizationPlan).where(OptimizationPlan.solver_plan_id == plan_id))).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    result = OptimizeResponse.model_validate(plan.result_json)
    evidence = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    explanation = _deterministic_explanation(result)
    generated_by = "deterministic"
    try:
        candidate = await LLMService(settings, tracer=Tracer(session_factory=AsyncSessionLocal, settings=settings)).generate_grounded_answer(
            system_prompt=(
                "Explain only the supplied OR-Tools advisory plan. Do not recalculate, invent numbers, "
                "dispatch resources, or imply approval. State key constraints, risks, and alternatives. "
                "Use [O1] for every factual claim."
            ),
            user_prompt=f"Optimization evidence O1:\n{evidence}",
            temperature=0,
            max_output_tokens=700,
        )
        if "[O1]" in candidate and _numbers_are_grounded(candidate, evidence):
            explanation = candidate
            generated_by = "llm"
    except LLMError:
        pass
    return PlanExplanation(
        plan_id=plan_id,
        explanation=explanation,
        generated_by=generated_by,
    )
