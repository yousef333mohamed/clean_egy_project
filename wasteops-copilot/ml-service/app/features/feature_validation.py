"""Feature-frame validation that never coerces missing measurements to zero."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from app.features.feature_registry import definitions_for


@dataclass(frozen=True)
class ValidationResult:
    frame: pd.DataFrame
    warnings: list[str]
    missing_rate: float


def validate_feature_frame(frame: pd.DataFrame, model_name: str, as_of: datetime) -> ValidationResult:
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    result = frame.copy()
    warnings: list[str] = []
    required = definitions_for(model_name)
    for definition in required:
        if definition.feature_name not in result:
            result[definition.feature_name] = pd.NA
            warnings.append(f"Missing feature: {definition.feature_name}")
        if definition.nullable:
            result[f"{definition.feature_name}__missing"] = result[definition.feature_name].isna().astype(int)
        elif result[definition.feature_name].isna().any():
            raise ValueError(f"Required feature is missing: {definition.feature_name}")
        rules = definition.validation_rules
        numeric = pd.to_numeric(result[definition.feature_name], errors="coerce")
        if "min" in rules and (numeric.dropna() < rules["min"]).any():
            raise ValueError(f"Feature below expected range: {definition.feature_name}")
        if "max" in rules and (numeric.dropna() > rules["max"]).any():
            raise ValueError(f"Feature above expected range: {definition.feature_name}")
    missing_rate = float(result[[f.feature_name for f in required]].isna().mean().mean()) if required and len(result) else 0.0
    result.attrs["as_of"] = as_of.astimezone(timezone.utc).isoformat()
    return ValidationResult(result, warnings, missing_rate)


def enforce_point_in_time(frame: pd.DataFrame, timestamp_column: str, as_of: datetime) -> pd.DataFrame:
    timestamps = pd.to_datetime(frame[timestamp_column], utc=True, errors="raise")
    cutoff = pd.Timestamp(as_of).tz_convert("UTC") if pd.Timestamp(as_of).tzinfo else pd.Timestamp(as_of, tz="UTC")
    if (timestamps > cutoff).any():
        raise ValueError("Temporal leakage detected: feature row occurs after prediction timestamp")
    return frame.loc[timestamps <= cutoff].copy()
