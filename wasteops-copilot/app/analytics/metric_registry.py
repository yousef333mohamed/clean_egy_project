"""Typed allow-list of operational metrics and their SQL expressions."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.sql.elements import ColumnElement

from app.analytics.enums import AggregationType, AnalyticsDomain
from app.models.environmental_daily import EnvironmentalDaily
from app.models.operational_daily import OperationalDaily
from app.models.smart_bin import SmartBin
from app.models.smart_bin_reading import SmartBinReading
from app.models.truck import Truck
from app.models.truck_trip_log import TruckTripLog
from app.models.worker import Worker
from app.models.workforce_attendance import WorkforceAttendance

LOW_BATTERY_THRESHOLD_PCT = 20
CRITICAL_FILL_THRESHOLD_PCT = 80


def null_safe_average(values: list[Decimal | int | float | None]) -> tuple[Decimal | None, int, int]:
    """Return mean, included count, and null-excluded count without zero filling."""
    valid = [Decimal(str(value)) for value in values if value is not None]
    return ((sum(valid, Decimal(0)) / len(valid)) if valid else None, len(valid), len(values) - len(valid))


def truck_utilization_pct(load_kg: Decimal | float | int, capacity_kg: Decimal | float | int) -> Decimal | None:
    """Return uncapped utilization; invalid/zero capacity has no result."""
    capacity = Decimal(str(capacity_kg))
    return None if capacity <= 0 else Decimal(str(load_kg)) / capacity * 100


def fuel_efficiency_km_per_l(distance_km: Decimal | float | int, fuel_l: Decimal | float | int) -> Decimal | None:
    """Return distance/fuel only for positive fuel."""
    fuel = Decimal(str(fuel_l))
    return None if fuel <= 0 else Decimal(str(distance_km)) / fuel


def attendance_rate_pct(present_count: int, record_count: int) -> Decimal | None:
    """Return present/records × 100 without inventing a zero rate for no data."""
    return None if record_count <= 0 else Decimal(present_count) / Decimal(record_count) * 100


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    name: str
    domain: AnalyticsDomain
    source_models: tuple[str, ...]
    description: str
    unit: str
    allowed_aggregations: tuple[AggregationType, ...]
    supported_filters: tuple[str, ...]
    default_aggregation: AggregationType
    nullable_behavior: str
    zero_and_null_differ: bool
    expression_builder: Callable[[], ColumnElement[Any]]
    interpretation_notes: str


def _metric(
    metric_id: str,
    name: str,
    domain: AnalyticsDomain,
    sources: tuple[str, ...],
    description: str,
    unit: str,
    aggregation: AggregationType,
    builder: Callable[[], ColumnElement[Any]],
    *,
    filters: tuple[str, ...] = ("start_date", "end_date", "region"),
    nullable: str = "No nullable inputs.",
    zero_null: bool = True,
    notes: str = "Historical operational metric; not a prediction.",
) -> MetricDefinition:
    return MetricDefinition(metric_id, name, domain, sources, description, unit, (aggregation,), filters, aggregation, nullable, zero_null, builder, notes)


METRICS = [
    _metric(
        "bin_count",
        "Bin count",
        AnalyticsDomain.BINS,
        ("SmartBin",),
        "Distinct installed bins.",
        "bins",
        AggregationType.COUNT,
        lambda: func.count(func.distinct(SmartBin.bin_id)),
    ),
    _metric(
        "reading_count",
        "Reading count",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Telemetry record count.",
        "readings",
        AggregationType.COUNT,
        lambda: func.count(SmartBinReading.id),
    ),
    _metric(
        "average_fill_level_pct",
        "Average fill level",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Mean non-null fill level.",
        "%",
        AggregationType.AVERAGE,
        lambda: func.avg(SmartBinReading.fill_level_pct),
        nullable="Null fill values are excluded and reported.",
    ),
    _metric(
        "maximum_fill_level_pct",
        "Maximum fill level",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Maximum non-null fill level.",
        "%",
        AggregationType.MAXIMUM,
        lambda: func.max(SmartBinReading.fill_level_pct),
        nullable="Null fill values are excluded and reported.",
    ),
    _metric(
        "average_waste_weight_kg",
        "Average waste weight",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Mean non-null waste weight.",
        "kg",
        AggregationType.AVERAGE,
        lambda: func.avg(SmartBinReading.waste_weight_kg),
        nullable="Null weights are excluded and reported.",
    ),
    _metric(
        "average_battery_level_pct",
        "Average battery level",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Mean battery level.",
        "%",
        AggregationType.AVERAGE,
        lambda: func.avg(SmartBinReading.battery_level_pct),
    ),
    _metric(
        "low_battery_reading_count",
        "Low-battery readings",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Readings below the configured battery rule.",
        "readings",
        AggregationType.COUNT,
        lambda: func.sum(case((SmartBinReading.battery_level_pct < LOW_BATTERY_THRESHOLD_PCT, 1), else_=0)),
        notes="Configured rule: battery < 20%; not marked as official policy.",
    ),
    _metric(
        "sensor_fault_reading_count",
        "Sensor-fault readings",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Readings whose status indicates a fault.",
        "readings",
        AggregationType.COUNT,
        lambda: func.sum(case((func.lower(SmartBinReading.sensor_status).like("%fault%"), 1), else_=0)),
    ),
    _metric(
        "collection_event_count",
        "Collection events",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Readings marked collected.",
        "events",
        AggregationType.COUNT,
        lambda: func.sum(case((SmartBinReading.was_collected.is_(True), 1), else_=0)),
    ),
    _metric(
        "critical_fill_reading_count",
        "Critical-fill readings",
        AnalyticsDomain.BINS,
        ("SmartBinReading",),
        "Readings at or above the configured fill rule.",
        "readings",
        AggregationType.COUNT,
        lambda: func.sum(case((SmartBinReading.fill_level_pct >= CRITICAL_FILL_THRESHOLD_PCT, 1), else_=0)),
        notes="Configured rule: fill >= 80%; not marked as official policy.",
    ),
    _metric(
        "missed_collection_count",
        "Missed collections",
        AnalyticsDomain.OPERATIONS,
        ("OperationalDaily",),
        "Missed-collection flags.",
        "records",
        AggregationType.COUNT,
        lambda: func.sum(case((OperationalDaily.missed_collection.is_(True), 1), else_=0)),
    ),
    _metric(
        "emergency_request_count",
        "Emergency requests",
        AnalyticsDomain.OPERATIONS,
        ("OperationalDaily",),
        "Emergency-request flags.",
        "records",
        AggregationType.COUNT,
        lambda: func.sum(case((OperationalDaily.emergency_request.is_(True), 1), else_=0)),
    ),
    _metric(
        "complaint_count",
        "Complaints",
        AnalyticsDomain.OPERATIONS,
        ("OperationalDaily",),
        "Complaint flags.",
        "records",
        AggregationType.COUNT,
        lambda: func.sum(case((OperationalDaily.complaint_filed.is_(True), 1), else_=0)),
    ),
    _metric(
        "illegal_dumping_count",
        "Illegal-dumping flags",
        AnalyticsDomain.OPERATIONS,
        ("OperationalDaily",),
        "Illegal-dumping flags.",
        "records",
        AggregationType.COUNT,
        lambda: func.sum(case((OperationalDaily.illegal_dumping_flag.is_(True), 1), else_=0)),
    ),
    _metric(
        "average_service_completion_time_min",
        "Average completion time",
        AnalyticsDomain.OPERATIONS,
        ("OperationalDaily",),
        "Mean non-null service-completion time.",
        "minutes",
        AggregationType.AVERAGE,
        lambda: func.avg(OperationalDaily.service_completion_time_min),
        nullable="Null completion times are excluded and reported.",
    ),
    _metric(
        "completed_service_record_count",
        "Completed service records",
        AnalyticsDomain.OPERATIONS,
        ("OperationalDaily",),
        "Records with a completion time.",
        "records",
        AggregationType.COUNT,
        lambda: func.count(OperationalDaily.service_completion_time_min),
    ),
    _metric(
        "truck_count",
        "Truck count",
        AnalyticsDomain.TRUCKS,
        ("Truck",),
        "Distinct trucks.",
        "trucks",
        AggregationType.COUNT,
        lambda: func.count(func.distinct(Truck.truck_id)),
    ),
    _metric(
        "trip_count",
        "Trip count",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Trip record count.",
        "trips",
        AggregationType.COUNT,
        lambda: func.count(TruckTripLog.id),
    ),
    _metric(
        "total_distance_km",
        "Total distance",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Sum of trip distance.",
        "km",
        AggregationType.SUM,
        lambda: func.sum(TruckTripLog.distance_km),
    ),
    _metric(
        "average_distance_km",
        "Average distance",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Mean trip distance.",
        "km",
        AggregationType.AVERAGE,
        lambda: func.avg(TruckTripLog.distance_km),
    ),
    _metric(
        "total_fuel_consumed_l",
        "Total fuel",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Sum of fuel consumed.",
        "litres",
        AggregationType.SUM,
        lambda: func.sum(TruckTripLog.fuel_consumed_l),
    ),
    _metric(
        "average_fuel_consumed_l",
        "Average fuel",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Mean trip fuel.",
        "litres",
        AggregationType.AVERAGE,
        lambda: func.avg(TruckTripLog.fuel_consumed_l),
    ),
    _metric(
        "average_load_kg",
        "Average load",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Mean trip load.",
        "kg",
        AggregationType.AVERAGE,
        lambda: func.avg(TruckTripLog.load_kg),
    ),
    _metric(
        "average_speed_kmh",
        "Average speed",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Mean recorded speed.",
        "km/h",
        AggregationType.AVERAGE,
        lambda: func.avg(TruckTripLog.avg_speed_kmh),
    ),
    _metric(
        "total_stops_completed",
        "Stops completed",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Sum of completed stops.",
        "stops",
        AggregationType.SUM,
        lambda: func.sum(TruckTripLog.stops_completed),
    ),
    _metric(
        "average_trip_duration_min",
        "Average trip duration",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Mean trip duration.",
        "minutes",
        AggregationType.AVERAGE,
        lambda: func.avg(TruckTripLog.trip_duration_min),
    ),
    _metric(
        "truck_utilization_pct",
        "Truck utilization",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog", "Truck"),
        "Average load/capacity × 100 for valid capacity.",
        "%",
        AggregationType.RATIO,
        lambda: func.avg(TruckTripLog.load_kg * 100.0 / func.nullif(Truck.capacity_kg, 0)),
        notes="Values above 100% remain visible as deterministic anomalies.",
    ),
    _metric(
        "fuel_efficiency_km_per_l",
        "Fuel efficiency",
        AnalyticsDomain.TRUCKS,
        ("TruckTripLog",),
        "Distance per litre when fuel is positive.",
        "km/l",
        AggregationType.RATIO,
        lambda: func.avg(case((TruckTripLog.fuel_consumed_l > 0, TruckTripLog.distance_km / TruckTripLog.fuel_consumed_l), else_=None)),
        nullable="Trips with zero fuel are excluded and reported.",
    ),
    _metric(
        "worker_count",
        "Worker count",
        AnalyticsDomain.WORKFORCE,
        ("Worker",),
        "Distinct workers.",
        "workers",
        AggregationType.COUNT,
        lambda: func.count(func.distinct(Worker.worker_id)),
    ),
    _metric(
        "attendance_record_count",
        "Attendance records",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Attendance row count.",
        "records",
        AggregationType.COUNT,
        lambda: func.count(WorkforceAttendance.id),
    ),
    _metric(
        "present_worker_count",
        "Present records",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Present attendance records.",
        "records",
        AggregationType.COUNT,
        lambda: func.sum(case((WorkforceAttendance.present.is_(True), 1), else_=0)),
    ),
    _metric(
        "absent_worker_count",
        "Absent records",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Absent attendance records.",
        "records",
        AggregationType.COUNT,
        lambda: func.sum(case((WorkforceAttendance.present.is_(False), 1), else_=0)),
    ),
    _metric(
        "attendance_rate_pct",
        "Attendance rate",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Present records / attendance records × 100.",
        "%",
        AggregationType.RATIO,
        lambda: func.avg(case((WorkforceAttendance.present.is_(True), 100.0), else_=0.0)),
    ),
    _metric(
        "total_completed_tasks",
        "Completed tasks",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Sum of completed tasks.",
        "tasks",
        AggregationType.SUM,
        lambda: func.sum(WorkforceAttendance.completed_tasks),
    ),
    _metric(
        "average_completed_tasks",
        "Average completed tasks",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Mean completed tasks.",
        "tasks",
        AggregationType.AVERAGE,
        lambda: func.avg(WorkforceAttendance.completed_tasks),
    ),
    _metric(
        "total_overtime_hours",
        "Overtime",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Sum of overtime hours.",
        "hours",
        AggregationType.SUM,
        lambda: func.sum(WorkforceAttendance.overtime_hours),
    ),
    _metric(
        "average_performance_score",
        "Average performance",
        AnalyticsDomain.WORKFORCE,
        ("WorkforceAttendance",),
        "Mean non-null performance score.",
        "score",
        AggregationType.AVERAGE,
        lambda: func.avg(WorkforceAttendance.performance_score),
        nullable="Missing scores are excluded and reported.",
    ),
    _metric(
        "average_temperature_c",
        "Average temperature",
        AnalyticsDomain.ENVIRONMENT,
        ("EnvironmentalDaily",),
        "Mean region-day temperature.",
        "°C",
        AggregationType.AVERAGE,
        lambda: func.avg(EnvironmentalDaily.temperature_c),
        notes="Aggregated at region-day level.",
    ),
    _metric(
        "total_rainfall_mm",
        "Total rainfall",
        AnalyticsDomain.ENVIRONMENT,
        ("EnvironmentalDaily",),
        "Sum of region-day rainfall.",
        "mm",
        AggregationType.SUM,
        lambda: func.sum(EnvironmentalDaily.rainfall_mm),
        notes="Aggregated at region-day level.",
    ),
    _metric(
        "holiday_day_count",
        "Holiday region-days",
        AnalyticsDomain.ENVIRONMENT,
        ("EnvironmentalDaily",),
        "Holiday region-day records.",
        "region-days",
        AggregationType.COUNT,
        lambda: func.sum(case((EnvironmentalDaily.is_holiday.is_(True), 1), else_=0)),
        notes="Counts region-day records, not distinct calendar days.",
    ),
    _metric(
        "festival_day_count",
        "Festival region-days",
        AnalyticsDomain.ENVIRONMENT,
        ("EnvironmentalDaily",),
        "Festival region-day records.",
        "region-days",
        AggregationType.COUNT,
        lambda: func.sum(case((EnvironmentalDaily.is_festival.is_(True), 1), else_=0)),
        notes="Counts region-day records, not distinct calendar days.",
    ),
    _metric(
        "weekend_day_count",
        "Weekend region-days",
        AnalyticsDomain.ENVIRONMENT,
        ("EnvironmentalDaily",),
        "Weekend region-day records.",
        "region-days",
        AggregationType.COUNT,
        lambda: func.sum(case((EnvironmentalDaily.is_weekend.is_(True), 1), else_=0)),
        notes="Counts region-day records, not distinct calendar days.",
    ),
    _metric(
        "traffic_level_distribution",
        "Traffic distribution",
        AnalyticsDomain.ENVIRONMENT,
        ("EnvironmentalDaily",),
        "Counts grouped by traffic level.",
        "region-days",
        AggregationType.DISTRIBUTION,
        lambda: func.count(EnvironmentalDaily.id),
        notes="Aggregated at region-day level.",
    ),
]

METRIC_REGISTRY = {metric.metric_id: metric for metric in METRICS}


def get_metric(metric_id: str) -> MetricDefinition:
    """Return only a registered metric."""
    try:
        return METRIC_REGISTRY[metric_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported metric: {metric_id}") from exc
