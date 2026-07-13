"""Create the WasteOps database foundation.

Revision ID: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable pgvector and create all Step 2 tables."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "smart_bins",
        sa.Column("bin_id", sa.String(120), nullable=False),
        sa.Column("governorate", sa.String(120), nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("capacity_liters", sa.Integer(), nullable=False),
        sa.Column("primary_waste_type", sa.String(60), nullable=False),
        sa.Column("install_date", sa.Date(), nullable=False),
        sa.CheckConstraint("capacity_liters > 0", name="ck_smart_bins_capacity_positive"),
        sa.PrimaryKeyConstraint("bin_id"),
        sa.UniqueConstraint("bin_id", name="uq_smart_bins_bin_id"),
    )
    op.create_index("ix_smart_bins_bin_id", "smart_bins", ["bin_id"], unique=True)

    op.create_table(
        "trucks",
        sa.Column("truck_id", sa.String(50), nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("capacity_kg", sa.Integer(), nullable=False),
        sa.Column("model_year", sa.Integer(), nullable=False),
        sa.Column("fuel_type", sa.String(40), nullable=False),
        sa.CheckConstraint("capacity_kg > 0", name="ck_trucks_capacity_positive"),
        sa.CheckConstraint("model_year BETWEEN 1980 AND 2100", name="ck_trucks_model_year_reasonable"),
        sa.PrimaryKeyConstraint("truck_id"),
        sa.UniqueConstraint("truck_id", name="uq_trucks_truck_id"),
    )
    op.create_index("ix_trucks_truck_id", "trucks", ["truck_id"], unique=True)

    op.create_table(
        "workers",
        sa.Column("worker_id", sa.String(120), nullable=False),
        sa.Column("governorate", sa.String(120), nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("shift", sa.String(40), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.CheckConstraint("experience_years >= 0", name="ck_workers_experience_nonnegative"),
        sa.PrimaryKeyConstraint("worker_id"),
        sa.UniqueConstraint("worker_id", name="uq_workers_worker_id"),
    )
    op.create_index("ix_workers_worker_id", "workers", ["worker_id"], unique=True)

    op.create_table(
        "environmental_daily",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=False),
        sa.Column("rainfall_mm", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_holiday", sa.Boolean(), nullable=False),
        sa.Column("is_festival", sa.Boolean(), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), nullable=False),
        sa.Column("traffic_level", sa.String(40), nullable=False),
        sa.CheckConstraint("rainfall_mm >= 0", name="ck_environmental_daily_rainfall_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "region", name="uq_environmental_daily_date_region"),
    )
    op.create_index("ix_environmental_daily_date", "environmental_daily", ["date"])
    op.create_index("ix_environmental_daily_region", "environmental_daily", ["region"])
    op.create_index("ix_environmental_daily_traffic_level", "environmental_daily", ["traffic_level"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.String(120), nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=True),
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("asset_type", sa.String(120), nullable=True),
        sa.Column("region", sa.String(120), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("version", sa.String(40), nullable=True),
        sa.Column("chunk_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(btrim(content)) > 0", name="ck_document_chunks_content_not_empty"),
        sa.CheckConstraint("chunk_number >= 0", name="ck_document_chunks_chunk_number_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_number", name="uq_document_chunks_document_chunk"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_source_filename", "document_chunks", ["source_filename"])

    op.create_table(
        "smart_bin_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bin_id", sa.String(120), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fill_level_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("waste_weight_kg", sa.Numeric(12, 3), nullable=False),
        sa.Column("waste_type", sa.String(60), nullable=False),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=False),
        sa.Column("humidity_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("battery_level_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("sensor_status", sa.String(40), nullable=False),
        sa.Column("was_collected", sa.Boolean(), nullable=False),
        sa.CheckConstraint("fill_level_pct BETWEEN 0 AND 100", name="ck_smart_bin_readings_fill_pct"),
        sa.CheckConstraint("humidity_pct BETWEEN 0 AND 100", name="ck_smart_bin_readings_humidity_pct"),
        sa.CheckConstraint("battery_level_pct BETWEEN 0 AND 100", name="ck_smart_bin_readings_battery_pct"),
        sa.CheckConstraint("waste_weight_kg >= 0", name="ck_smart_bin_readings_weight_nonnegative"),
        sa.ForeignKeyConstraint(["bin_id"], ["smart_bins.bin_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bin_id", "timestamp", name="uq_smart_bin_readings_bin_timestamp"),
    )
    op.create_index("ix_smart_bin_readings_bin_timestamp", "smart_bin_readings", ["bin_id", "timestamp"])
    op.create_index("ix_smart_bin_readings_timestamp", "smart_bin_readings", ["timestamp"])
    op.create_index("ix_smart_bin_readings_sensor_status", "smart_bin_readings", ["sensor_status"])
    op.create_index("ix_smart_bin_readings_was_collected", "smart_bin_readings", ["was_collected"])

    op.create_table(
        "operational_daily",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bin_id", sa.String(120), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("governorate", sa.String(120), nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("missed_collection", sa.Boolean(), nullable=False),
        sa.Column("emergency_request", sa.Boolean(), nullable=False),
        sa.Column("complaint_filed", sa.Boolean(), nullable=False),
        sa.Column("illegal_dumping_flag", sa.Boolean(), nullable=False),
        sa.Column("service_completion_time_min", sa.Numeric(10, 2), nullable=True),
        sa.CheckConstraint(
            "service_completion_time_min IS NULL OR service_completion_time_min >= 0",
            name="ck_operational_daily_completion_nonnegative",
        ),
        sa.ForeignKeyConstraint(["bin_id"], ["smart_bins.bin_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bin_id", "date", name="uq_operational_daily_bin_date"),
    )
    op.create_index("ix_operational_daily_date", "operational_daily", ["date"])
    op.create_index("ix_operational_daily_region", "operational_daily", ["region"])
    op.create_index("ix_operational_daily_missed_collection", "operational_daily", ["missed_collection"])
    op.create_index("ix_operational_daily_emergency_request", "operational_daily", ["emergency_request"])

    op.create_table(
        "truck_trip_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("truck_id", sa.String(50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("distance_km", sa.Numeric(12, 2), nullable=False),
        sa.Column("fuel_consumed_l", sa.Numeric(12, 2), nullable=False),
        sa.Column("load_kg", sa.Numeric(12, 2), nullable=False),
        sa.Column("avg_speed_kmh", sa.Numeric(8, 2), nullable=False),
        sa.Column("stops_completed", sa.Integer(), nullable=False),
        sa.Column("trip_duration_min", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("distance_km >= 0", name="ck_truck_trip_logs_distance_nonnegative"),
        sa.CheckConstraint("fuel_consumed_l >= 0", name="ck_truck_trip_logs_fuel_nonnegative"),
        sa.CheckConstraint("load_kg >= 0", name="ck_truck_trip_logs_load_nonnegative"),
        sa.CheckConstraint("avg_speed_kmh >= 0", name="ck_truck_trip_logs_speed_nonnegative"),
        sa.CheckConstraint("stops_completed >= 0", name="ck_truck_trip_logs_stops_nonnegative"),
        sa.CheckConstraint("trip_duration_min >= 0", name="ck_truck_trip_logs_duration_nonnegative"),
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.truck_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("truck_id", "date", name="uq_truck_trip_logs_truck_date"),
    )
    op.create_index("ix_truck_trip_logs_truck_id", "truck_trip_logs", ["truck_id"])
    op.create_index("ix_truck_trip_logs_date", "truck_trip_logs", ["date"])
    op.create_index("ix_truck_trip_logs_region", "truck_trip_logs", ["region"])
    op.create_index("ix_truck_trip_logs_status", "truck_trip_logs", ["status"])

    op.create_table(
        "workforce_attendance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("worker_id", sa.String(120), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("present", sa.Boolean(), nullable=False),
        sa.Column("completed_tasks", sa.Integer(), nullable=False),
        sa.Column("overtime_hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("performance_score", sa.Numeric(5, 2), nullable=False),
        sa.CheckConstraint("completed_tasks >= 0", name="ck_workforce_attendance_tasks_nonnegative"),
        sa.CheckConstraint("overtime_hours >= 0", name="ck_workforce_attendance_overtime_nonnegative"),
        sa.CheckConstraint("performance_score BETWEEN 0 AND 100", name="ck_workforce_attendance_performance_score"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.worker_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worker_id", "date", name="uq_workforce_attendance_worker_date"),
    )
    op.create_index("ix_workforce_attendance_worker_id", "workforce_attendance", ["worker_id"])
    op.create_index("ix_workforce_attendance_date", "workforce_attendance", ["date"])
    op.create_index("ix_workforce_attendance_present", "workforce_attendance", ["present"])


def downgrade() -> None:
    """Drop tables in dependency order, preserving the shared vector extension."""
    op.drop_table("workforce_attendance")
    op.drop_table("truck_trip_logs")
    op.drop_table("operational_daily")
    op.drop_table("smart_bin_readings")
    op.drop_table("document_chunks")
    op.drop_table("environmental_daily")
    op.drop_table("workers")
    op.drop_table("trucks")
    op.drop_table("smart_bins")
