"""Validated, idempotent CSV ingestion."""

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Date, DateTime
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.attendance import Attendance
from app.models.bin import SmartBin, SmartBinReading
from app.models.environment import EnvironmentalDaily
from app.models.operation import OperationalDaily
from app.models.trip import TruckTrip
from app.models.truck import Truck
from app.models.workforce import Worker
from app.schemas.ingestion import FileIngestionSummary, IngestionSummary
from app.utils.validators import normalize_column_name

logger = get_logger(__name__)
MODEL_MAP = {
    "smart_bins.csv": SmartBin,
    "trucks.csv": Truck,
    "workforce.csv": Worker,
    "smart_bin_readings.csv": SmartBinReading,
    "truck_trip_logs.csv": TruckTrip,
    "workforce_attendance.csv": Attendance,
    "operational_daily.csv": OperationalDaily,
    "environmental_daily.csv": EnvironmentalDaily,
}
LOAD_ORDER = tuple(MODEL_MAP)


def _clean_value(value: Any) -> Any:
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    return value.item() if hasattr(value, "item") else value


class CSVLoader:
    """Load known WasteOps CSV datasets into PostgreSQL."""

    def __init__(self, session: AsyncSession, raw_dir: Path) -> None:
        self.session = session
        self.raw_dir = raw_dir

    async def ingest(self, filenames: list[str] | None = None) -> IngestionSummary:
        selected = filenames or list(LOAD_ORDER)
        selected.sort(key=lambda name: LOAD_ORDER.index(name) if name in LOAD_ORDER else len(LOAD_ORDER))
        summaries = [await self.ingest_file(name) for name in selected]
        return IngestionSummary(
            files=summaries,
            inserted_rows=sum(x.inserted_rows for x in summaries),
            duplicate_rows=sum(x.duplicate_rows for x in summaries),
            failed_rows=sum(x.failed_rows for x in summaries),
        )

    async def ingest_file(self, filename: str) -> FileIngestionSummary:
        summary = FileIngestionSummary(filename=filename)
        model = MODEL_MAP.get(filename)
        path = (self.raw_dir / filename).resolve()
        if model is None or path.parent != self.raw_dir.resolve() or not path.is_file():
            summary.failed_rows = 1
            summary.errors.append("Unknown or missing CSV file")
            return summary
        try:
            frame = pd.read_csv(path, encoding="utf-8")
            frame.columns = [normalize_column_name(c) for c in frame.columns]
        except Exception as exc:
            summary.failed_rows = 1
            summary.errors.append(f"Unable to read CSV: {exc}")
            return summary
        required = {c.name for c in model.__table__.columns if not c.primary_key or not c.autoincrement}
        required.discard("id")
        missing = required - set(frame.columns)
        if missing:
            summary.failed_rows = len(frame)
            summary.total_rows = len(frame)
            summary.errors.append(f"Missing required columns: {sorted(missing)}")
            return summary
        summary.total_rows = len(frame)
        date_columns = {c.name: c.type for c in model.__table__.columns if isinstance(c.type, (Date, DateTime))}
        for index, raw in frame.iterrows():
            record = {key: _clean_value(value) for key, value in raw.to_dict().items() if key in required}
            try:
                for key, column_type in date_columns.items():
                    if record.get(key) is not None:
                        parsed = pd.to_datetime(record[key], errors="raise")
                        record[key] = parsed.to_pydatetime() if isinstance(column_type, DateTime) else parsed.date()
                result = await self.session.execute(insert(model).values(**record).on_conflict_do_nothing())
                if result.rowcount:
                    summary.inserted_rows += 1
                else:
                    summary.duplicate_rows += 1
            except Exception as exc:
                await self.session.rollback()
                summary.failed_rows += 1
                message = f"row {index + 2}: {type(exc).__name__}: {exc}"
                summary.errors.append(message)
                logger.error("csv_row_failed", file=filename, row=index + 2, error=str(exc))
            else:
                await self.session.commit()
        logger.info("csv_ingested", **summary.model_dump(exclude={"errors"}))
        return summary
