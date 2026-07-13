"""Dataset versioning and point-in-time overflow target construction."""

import hashlib
import pandas as pd


def dataset_version(frame: pd.DataFrame) -> str:
    normalized = frame.sort_index(axis=1).sort_values(list(frame.columns), kind="stable").to_csv(index=False)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def overflow_targets(readings: pd.DataFrame, horizon_hours: int, critical_threshold_pct: float) -> pd.Series:
    if horizon_hours not in {6, 12, 24}:
        raise ValueError("Unsupported prediction horizon")
    frame = readings.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    result = pd.Series(False, index=frame.index, dtype=bool)
    for _, group in frame.sort_values("timestamp").groupby("bin_id"):
        times = group["timestamp"]
        fills = pd.to_numeric(group["fill_level_pct"], errors="coerce")
        for idx, when in times.items():
            future = fills[(times > when) & (times <= when + pd.Timedelta(hours=horizon_hours))]
            result.loc[idx] = bool((future >= critical_threshold_pct).any())
    return result


def assert_features_available_before(frame: pd.DataFrame, feature_timestamp: str, prediction_timestamp: str) -> None:
    feature = pd.to_datetime(frame[feature_timestamp], utc=True)
    prediction = pd.to_datetime(frame[prediction_timestamp], utc=True)
    if (feature > prediction).any():
        raise ValueError("Temporal leakage detected")
