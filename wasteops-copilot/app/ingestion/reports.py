"""Rejected-row CSV reporting and JSON-safe source records."""

import csv
import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(slots=True)
class RejectedRecord:
    """One invalid source row."""

    row_number: int
    error_code: str
    error_message: str
    raw_record: dict[str, Any]


def json_safe_record(record: dict[str, Any]) -> dict[str, Any]:
    """Convert pandas values into valid JSONB-compatible primitives."""
    safe: dict[str, Any] = {}
    for key, value in record.items():
        if key == "__source_row_number__":
            continue
        try:
            missing = value is None or bool(pd.isna(value))
        except (TypeError, ValueError):
            missing = False
        if missing or (isinstance(value, float) and math.isnan(value)):
            safe[key] = None
        elif isinstance(value, (datetime, date, Decimal)):
            safe[key] = str(value)
        elif hasattr(value, "item"):
            safe[key] = value.item()
        else:
            safe[key] = value
    return safe


def write_rejection_report(rejected_dir: Path, dataset: str, run_id: object, records: list[RejectedRecord]) -> Path | None:
    """Write a safe report only when rejected records exist."""
    if not records:
        return None
    rejected_dir.mkdir(parents=True, exist_ok=True)
    path = rejected_dir / f"{dataset}_{run_id}_rejected.csv"
    original_columns = list(dict.fromkeys(key for item in records for key in item.raw_record))
    fields = ["source_row_number", "error_code", "error_message", *original_columns]
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in records:
            writer.writerow(
                {
                    "source_row_number": item.row_number,
                    "error_code": item.error_code,
                    "error_message": item.error_message,
                    **item.raw_record,
                }
            )
    return path
