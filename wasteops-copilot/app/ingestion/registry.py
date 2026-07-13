"""Single source of truth for supported CSV datasets."""

from dataclasses import dataclass

from sqlalchemy.orm import DeclarativeBase

from app.models import (
    EnvironmentalDaily,
    OperationalDaily,
    SmartBin,
    SmartBinReading,
    Truck,
    TruckTripLog,
    Worker,
    WorkforceAttendance,
)


@dataclass(frozen=True, slots=True)
class ForeignKeyDefinition:
    """A child column and the parent model column it references."""

    column: str
    parent_model: type[DeclarativeBase]
    parent_column: str


@dataclass(frozen=True, slots=True)
class DatasetDefinition:
    """All parsing and storage metadata for a supported dataset."""

    name: str
    filenames: tuple[str, ...]
    model: type[DeclarativeBase]
    required_columns: tuple[str, ...]
    nullable_columns: frozenset[str]
    boolean_columns: frozenset[str]
    date_columns: frozenset[str]
    timestamp_columns: frozenset[str]
    integer_columns: frozenset[str]
    decimal_columns: frozenset[str]
    natural_key: tuple[str, ...]
    foreign_keys: tuple[ForeignKeyDefinition, ...] = ()
    batch_size: int = 5000
    ingestion_order: int = 0
    expected_rows: int | None = None

    @property
    def numeric_columns(self) -> frozenset[str]:
        """Return integer and decimal columns together."""
        return self.integer_columns | self.decimal_columns


def _files(name: str) -> tuple[str, str]:
    return f"{name}.csv", f"{name}(1).csv"


DATASET_REGISTRY: dict[str, DatasetDefinition] = {
    "smart_bins": DatasetDefinition(
        "smart_bins",
        _files("smart_bins"),
        SmartBin,
        ("bin_id", "governorate", "region", "latitude", "longitude", "capacity_liters", "primary_waste_type", "install_date"),
        frozenset(),
        frozenset(),
        frozenset({"install_date"}),
        frozenset(),
        frozenset({"capacity_liters"}),
        frozenset({"latitude", "longitude"}),
        ("bin_id",),
        batch_size=1000,
        ingestion_order=1,
        expected_rows=230,
    ),
    "trucks": DatasetDefinition(
        "trucks",
        _files("trucks"),
        Truck,
        ("truck_id", "region", "capacity_kg", "model_year", "fuel_type"),
        frozenset(),
        frozenset(),
        frozenset(),
        frozenset(),
        frozenset({"capacity_kg", "model_year"}),
        frozenset(),
        ("truck_id",),
        batch_size=1000,
        ingestion_order=2,
        expected_rows=17,
    ),
    "workforce": DatasetDefinition(
        "workforce",
        _files("workforce"),
        Worker,
        ("worker_id", "governorate", "region", "shift", "experience_years"),
        frozenset(),
        frozenset(),
        frozenset(),
        frozenset(),
        frozenset({"experience_years"}),
        frozenset(),
        ("worker_id",),
        batch_size=1000,
        ingestion_order=3,
        expected_rows=113,
    ),
    "environmental_daily": DatasetDefinition(
        "environmental_daily",
        _files("environmental_daily"),
        EnvironmentalDaily,
        ("date", "region", "temperature_c", "rainfall_mm", "is_holiday", "is_festival", "is_weekend", "traffic_level"),
        frozenset(),
        frozenset({"is_holiday", "is_festival", "is_weekend"}),
        frozenset({"date"}),
        frozenset(),
        frozenset(),
        frozenset({"temperature_c", "rainfall_mm"}),
        ("date", "region"),
        batch_size=1000,
        ingestion_order=4,
        expected_rows=450,
    ),
    "smart_bin_readings": DatasetDefinition(
        "smart_bin_readings",
        _files("smart_bin_readings"),
        SmartBinReading,
        (
            "bin_id",
            "timestamp",
            "fill_level_pct",
            "waste_weight_kg",
            "waste_type",
            "temperature_c",
            "humidity_pct",
            "battery_level_pct",
            "sensor_status",
            "was_collected",
        ),
        frozenset({"fill_level_pct", "waste_weight_kg"}),
        frozenset({"was_collected"}),
        frozenset(),
        frozenset({"timestamp"}),
        frozenset(),
        frozenset({"fill_level_pct", "waste_weight_kg", "temperature_c", "humidity_pct", "battery_level_pct"}),
        ("bin_id", "timestamp"),
        (ForeignKeyDefinition("bin_id", SmartBin, "bin_id"),),
        batch_size=5000,
        ingestion_order=5,
        expected_rows=165600,
    ),
    "operational_daily": DatasetDefinition(
        "operational_daily",
        _files("operational_daily"),
        OperationalDaily,
        (
            "bin_id",
            "date",
            "governorate",
            "region",
            "missed_collection",
            "emergency_request",
            "complaint_filed",
            "illegal_dumping_flag",
            "service_completion_time_min",
        ),
        frozenset({"service_completion_time_min"}),
        frozenset({"missed_collection", "emergency_request", "complaint_filed", "illegal_dumping_flag"}),
        frozenset({"date"}),
        frozenset(),
        frozenset(),
        frozenset({"service_completion_time_min"}),
        ("bin_id", "date"),
        (ForeignKeyDefinition("bin_id", SmartBin, "bin_id"),),
        batch_size=5000,
        ingestion_order=6,
        expected_rows=20700,
    ),
    "truck_trip_logs": DatasetDefinition(
        "truck_trip_logs",
        _files("truck_trip_logs"),
        TruckTripLog,
        ("truck_id", "date", "region", "status", "distance_km", "fuel_consumed_l", "load_kg", "avg_speed_kmh", "stops_completed", "trip_duration_min"),
        frozenset(),
        frozenset(),
        frozenset({"date"}),
        frozenset(),
        frozenset({"stops_completed"}),
        frozenset({"distance_km", "fuel_consumed_l", "load_kg", "avg_speed_kmh", "trip_duration_min"}),
        ("truck_id", "date"),
        (ForeignKeyDefinition("truck_id", Truck, "truck_id"),),
        batch_size=5000,
        ingestion_order=7,
        expected_rows=1530,
    ),
    "workforce_attendance": DatasetDefinition(
        "workforce_attendance",
        _files("workforce_attendance"),
        WorkforceAttendance,
        ("worker_id", "date", "present", "completed_tasks", "overtime_hours", "performance_score"),
        frozenset({"performance_score"}),
        frozenset({"present"}),
        frozenset({"date"}),
        frozenset(),
        frozenset({"completed_tasks"}),
        frozenset({"overtime_hours", "performance_score"}),
        ("worker_id", "date"),
        (ForeignKeyDefinition("worker_id", Worker, "worker_id"),),
        batch_size=5000,
        ingestion_order=8,
        expected_rows=10170,
    ),
}


def get_dataset(name: str) -> DatasetDefinition:
    """Return a definition without ever interpreting *name* as a path."""
    if name not in DATASET_REGISTRY:
        raise KeyError(name)
    return DATASET_REGISTRY[name]
