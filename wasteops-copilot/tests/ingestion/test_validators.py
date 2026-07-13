"""Dataset-specific nullable and range validation tests."""

import pytest

from app.ingestion.registry import get_dataset
from app.ingestion.validators import RecordValidationError, convert_record


def test_nullable_faulty_sensor_measurements_are_preserved() -> None:
    raw = {
        "bin_id": "B1",
        "timestamp": "2026-01-01T00:00:00",
        "fill_level_pct": None,
        "waste_weight_kg": None,
        "waste_type": "Mixed",
        "temperature_c": "20",
        "humidity_pct": "50",
        "battery_level_pct": "80",
        "sensor_status": "Fault",
        "was_collected": "false",
    }
    record = convert_record(raw, get_dataset("smart_bin_readings"), "Africa/Cairo")
    assert record["fill_level_pct"] is None
    assert record["waste_weight_kg"] is None


def test_invalid_percentage_is_rejected() -> None:
    raw = {
        "worker_id": "W1",
        "date": "2026-01-01",
        "present": True,
        "completed_tasks": 1,
        "overtime_hours": 0,
        "performance_score": 101,
    }
    with pytest.raises(RecordValidationError, match="between 0 and 100"):
        convert_record(raw, get_dataset("workforce_attendance"), "Africa/Cairo")


def test_nullable_operational_time_and_performance_score() -> None:
    operational = {
        "bin_id": "B1",
        "date": "2026-01-01",
        "governorate": "القاهرة",
        "region": "Cairo",
        "missed_collection": False,
        "emergency_request": False,
        "complaint_filed": False,
        "illegal_dumping_flag": False,
        "service_completion_time_min": None,
    }
    attendance = {
        "worker_id": "W1",
        "date": "2026-01-01",
        "present": False,
        "completed_tasks": 0,
        "overtime_hours": 0,
        "performance_score": None,
    }
    assert convert_record(operational, get_dataset("operational_daily"), "Africa/Cairo")["service_completion_time_min"] is None
    assert convert_record(attendance, get_dataset("workforce_attendance"), "Africa/Cairo")["performance_score"] is None
