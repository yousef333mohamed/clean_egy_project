"""Fixed, parameterized feature reads from the read-only analytics database."""

from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy import bindparam, text

from app.features.bin_features import build_bin_features


class FeatureRepository:
    def __init__(self, engine) -> None:
        self.engine = engine

    def _read(self, statement, parameters: dict) -> pd.DataFrame:
        if self.engine is None:
            raise RuntimeError("Analytics feature database is unavailable")
        with self.engine.connect() as connection:
            return pd.read_sql(statement, connection, params=parameters)

    def bins(self, bin_ids: list[str], as_of: datetime) -> pd.DataFrame:
        query = text("""
            SELECT r.bin_id, r.timestamp AS reading_timestamp, r.fill_level_pct, r.sensor_status,
                   r.was_collected, b.region
            FROM smart_bin_readings r JOIN smart_bins b ON b.bin_id = r.bin_id
            WHERE r.bin_id IN :ids AND r.timestamp <= :as_of AND r.timestamp >= :start
            ORDER BY r.bin_id, r.timestamp
        """).bindparams(bindparam("ids", expanding=True))
        rows = self._read(query, {"ids": bin_ids, "as_of": as_of, "start": as_of - timedelta(days=30)})
        if rows.empty:
            return rows
        rows["reading_timestamp"] = pd.to_datetime(rows["reading_timestamp"], utc=True)
        rows["last_collected_at"] = rows["reading_timestamp"].where(rows["was_collected"]).groupby(rows["bin_id"]).ffill()
        return build_bin_features(rows, as_of)

    def trucks(self, truck_ids: list[str], as_of: datetime) -> pd.DataFrame:
        query = text("""
            SELECT truck_id, date AS trip_date, fuel_consumed_l, distance_km, load_kg,
                   avg_speed_kmh, stops_completed, trip_duration_min
            FROM truck_trip_logs WHERE truck_id IN :ids AND date <= :as_of_date
            ORDER BY truck_id, date DESC
        """).bindparams(bindparam("ids", expanding=True))
        rows = self._read(query, {"ids": truck_ids, "as_of_date": as_of.date()})
        if rows.empty:
            return rows
        rows = rows.groupby("truck_id", as_index=False).first()
        fuel = pd.to_numeric(rows["fuel_consumed_l"], errors="coerce")
        rows["fuel_efficiency_km_per_l"] = pd.to_numeric(rows["distance_km"], errors="coerce") / fuel.where(fuel > 0)
        rows["feature_timestamp"] = pd.to_datetime(rows["trip_date"], utc=True) + pd.Timedelta(hours=23, minutes=59)
        return rows

    def missed_collections(self, regions: list[str], as_of: datetime) -> pd.DataFrame:
        query = text("""
            SELECT region,
              AVG(CASE WHEN missed_collection THEN 1.0 ELSE 0.0 END) AS historical_missed_rate_28d,
              SUM(CASE WHEN emergency_request THEN 1 ELSE 0 END) AS emergency_requests,
              SUM(CASE WHEN complaint_filed THEN 1 ELSE 0 END) AS complaints
            FROM operational_daily WHERE region IN :ids AND date < :as_of_date AND date >= :start_date GROUP BY region
        """).bindparams(bindparam("ids", expanding=True))
        rows = self._read(query, {"ids": regions, "as_of_date": as_of.date(), "start_date": as_of.date() - timedelta(days=28)})
        if not rows.empty:
            rows["critical_bin_count"] = 0
            rows["available_trucks"] = pd.NA
            rows["attendance_rate"] = pd.NA
            rows["feature_timestamp"] = pd.Timestamp(as_of.date() - timedelta(days=1), tz="UTC")
        return rows

    def workforce(self, regions: list[str], shifts: list[str], forecast_date: date, as_of: datetime) -> pd.DataFrame:
        query = text("""
            SELECT w.region, w.shift, AVG(a.completed_tasks) AS historical_task_volume,
              AVG(CASE WHEN a.present THEN 1.0 ELSE 0.0 END) AS attendance_rate,
              COUNT(DISTINCT CASE WHEN a.present THEN a.worker_id END) AS recent_required_workers_28d
            FROM workforce_attendance a JOIN workers w ON w.worker_id = a.worker_id
            WHERE w.region IN :regions AND w.shift IN :shifts AND a.date < :forecast_date AND a.date >= :start_date
            GROUP BY w.region, w.shift
        """).bindparams(bindparam("regions", expanding=True), bindparam("shifts", expanding=True))
        rows = self._read(query, {"regions": regions, "shifts": shifts, "forecast_date": forecast_date, "start_date": forecast_date - timedelta(days=28)})
        if not rows.empty:
            rows["expected_workload"] = rows["historical_task_volume"]
            rows["critical_bin_volume"] = pd.NA
            rows["truck_trips"] = pd.NA
            rows["feature_timestamp"] = pd.Timestamp(min(as_of.date(), forecast_date - timedelta(days=1)), tz="UTC")
        return rows
