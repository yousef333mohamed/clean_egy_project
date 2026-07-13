"""SQLAlchemy metadata and relationship tests."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, UniqueConstraint, inspect

from app.models import (
    Base,
    DocumentChunk,
    EnvironmentalDaily,
    OperationalDaily,
    SmartBin,
    SmartBinReading,
    Truck,
    TruckTripLog,
    Worker,
    WorkforceAttendance,
)


def _unique_column_sets(model: type[Base]) -> set[tuple[str, ...]]:
    return {tuple(column.name for column in constraint.columns) for constraint in model.__table__.constraints if isinstance(constraint, UniqueConstraint)}


def _check_sql(model: type[Base]) -> str:
    return " ".join(str(constraint.sqltext) for constraint in model.__table__.constraints if isinstance(constraint, CheckConstraint))


def test_model_table_names_are_registered() -> None:
    """Every required Step 2 table is present in Alembic metadata."""
    expected = {
        "smart_bins",
        "smart_bin_readings",
        "operational_daily",
        "environmental_daily",
        "trucks",
        "truck_trip_logs",
        "workers",
        "workforce_attendance",
        "document_chunks",
    }
    assert expected == set(Base.metadata.tables)


def test_composite_unique_constraints() -> None:
    """Dataset natural identities are protected against duplicates."""
    assert ("bin_id", "timestamp") in _unique_column_sets(SmartBinReading)
    assert ("bin_id", "date") in _unique_column_sets(OperationalDaily)
    assert ("date", "region") in _unique_column_sets(EnvironmentalDaily)
    assert ("truck_id", "date") in _unique_column_sets(TruckTripLog)
    assert ("worker_id", "date") in _unique_column_sets(WorkforceAttendance)
    assert ("document_id", "chunk_number") in _unique_column_sets(DocumentChunk)


def test_foreign_keys_target_parent_identifiers() -> None:
    """Only identifier-backed relationships create foreign keys."""
    assert {fk.target_fullname for fk in SmartBinReading.__table__.c.bin_id.foreign_keys} == {"smart_bins.bin_id"}
    assert {fk.target_fullname for fk in OperationalDaily.__table__.c.bin_id.foreign_keys} == {"smart_bins.bin_id"}
    assert {fk.target_fullname for fk in TruckTripLog.__table__.c.truck_id.foreign_keys} == {"trucks.truck_id"}
    assert {fk.target_fullname for fk in WorkforceAttendance.__table__.c.worker_id.foreign_keys} == {"workers.worker_id"}


def test_document_embedding_uses_configured_vector_type() -> None:
    """Document embeddings use pgvector rather than a generic array."""
    vector_type = DocumentChunk.__table__.c.embedding.type
    assert isinstance(vector_type, Vector)
    assert vector_type.dim == 1536


def test_relationships_have_back_populates_and_async_loading() -> None:
    """Parent-child mappings are bidirectional and avoid implicit async IO."""
    assert inspect(SmartBin).relationships.readings.back_populates == "smart_bin"
    assert inspect(SmartBin).relationships.operational_records.back_populates == "smart_bin"
    assert inspect(Truck).relationships.trip_logs.back_populates == "truck"
    assert inspect(Worker).relationships.attendance_records.back_populates == "worker"
    assert inspect(SmartBin).relationships.readings.lazy == "selectin"
    assert inspect(SmartBinReading).relationships.smart_bin.lazy == "raise"


def test_percentage_check_constraints_are_evidence_based() -> None:
    """Telemetry percentages and inspected performance scores are bounded."""
    reading_checks = _check_sql(SmartBinReading)
    assert "fill_level_pct BETWEEN 0 AND 100" in reading_checks
    assert "humidity_pct BETWEEN 0 AND 100" in reading_checks
    assert "battery_level_pct BETWEEN 0 AND 100" in reading_checks
    assert "performance_score BETWEEN 0 AND 100" in _check_sql(WorkforceAttendance)
