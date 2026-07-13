"""Chunked UTF-8 CSV reading with deterministic header validation."""

import csv
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.ingestion.registry import DatasetDefinition


class CsvSchemaError(ValueError):
    """The file header is unsafe or incompatible with its registry entry."""


@dataclass(frozen=True, slots=True)
class CsvSchema:
    """Normalized source columns and non-fatal warnings."""

    columns: tuple[str, ...]
    warnings: tuple[str, ...]


def normalize_header(value: str) -> str:
    """Trim a header and convert separators/casing to lowercase snake_case."""
    normalized = re.sub(r"[^\w]+", "_", value.strip(), flags=re.UNICODE)
    return re.sub(r"_+", "_", normalized).strip("_").lower()


def inspect_schema(path: Path, definition: DatasetDefinition, *, strict_columns: bool = False) -> CsvSchema:
    """Validate the raw header before pandas can mangle duplicate names."""
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        raw_columns = next(csv.reader(source), None)
    if not raw_columns:
        raise CsvSchemaError("CSV has no header")
    columns = tuple(normalize_header(column) for column in raw_columns)
    duplicates = sorted({column for column in columns if columns.count(column) > 1})
    if duplicates:
        raise CsvSchemaError(f"duplicate columns: {', '.join(duplicates)}")
    missing = sorted(set(definition.required_columns) - set(columns))
    if missing:
        raise CsvSchemaError(f"missing required columns: {', '.join(missing)}")
    unexpected = sorted(set(columns) - set(definition.required_columns))
    if unexpected and strict_columns:
        raise CsvSchemaError(f"unexpected columns: {', '.join(unexpected)}")
    warnings = (f"Unexpected columns: {', '.join(unexpected)}",) if unexpected else ()
    return CsvSchema(columns, warnings)


def read_csv_chunks(path: Path, definition: DatasetDefinition, batch_size: int, *, strict_columns: bool = False) -> tuple[CsvSchema, Iterator[pd.DataFrame]]:
    """Return validated schema and a lazy pandas chunk iterator."""
    schema = inspect_schema(path, definition, strict_columns=strict_columns)
    chunks = pd.read_csv(
        path,
        encoding="utf-8-sig",
        chunksize=batch_size,
        dtype=object,
        keep_default_na=True,
        na_values=["", " ", "NULL", "null", "NaN", "NaT"],
    )

    def normalized_chunks() -> Iterator[pd.DataFrame]:
        offset = 0
        for chunk in chunks:
            chunk.columns = list(schema.columns)
            chunk.insert(0, "__source_row_number__", range(offset + 2, offset + len(chunk) + 2))
            offset += len(chunk)
            yield chunk

    return schema, normalized_chunks()
