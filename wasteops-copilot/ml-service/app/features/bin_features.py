"""Point-in-time smart-bin feature generation."""

from datetime import datetime

import numpy as np
import pandas as pd

from app.features.feature_validation import enforce_point_in_time


def build_bin_features(readings: pd.DataFrame, as_of: datetime) -> pd.DataFrame:
    prior = enforce_point_in_time(readings, "reading_timestamp", as_of)
    if prior.empty:
        return pd.DataFrame()
    prior["reading_timestamp"] = pd.to_datetime(prior["reading_timestamp"], utc=True)
    output = []
    cutoff = pd.Timestamp(as_of)
    for bin_id, group in prior.sort_values("reading_timestamp").groupby("bin_id"):
        latest = group.iloc[-1]
        row: dict[str, object] = {"bin_id": bin_id, "feature_timestamp": latest["reading_timestamp"], "current_fill_level_pct": latest["fill_level_pct"]}
        for hours in (3, 6, 12, 24):
            window = group[group["reading_timestamp"] >= cutoff - pd.Timedelta(hours=hours)]
            row[f"fill_change_{hours}h"] = float(window["fill_level_pct"].iloc[-1] - window["fill_level_pct"].iloc[0]) if len(window) >= 2 else np.nan
        window24 = group[group["reading_timestamp"] >= cutoff - pd.Timedelta(hours=24)]
        row["maximum_fill_24h"] = float(window24["fill_level_pct"].max())
        elapsed = (window24["reading_timestamp"].iloc[-1] - window24["reading_timestamp"].iloc[0]).total_seconds() / 3600 if len(window24) >= 2 else 0
        row["average_fill_rate_24h"] = float((window24["fill_level_pct"].iloc[-1] - window24["fill_level_pct"].iloc[0]) / elapsed) if elapsed > 0 else np.nan
        last_collection = pd.to_datetime(latest.get("last_collected_at"), utc=True, errors="coerce")
        row["hours_since_last_collection"] = (cutoff - last_collection).total_seconds() / 3600 if not pd.isna(last_collection) else np.nan
        row["sensor_fault_flag"] = str(latest.get("sensor_status", "unknown")).casefold() == "fault"
        row["region"] = latest.get("region", "unknown")
        output.append(row)
    return pd.DataFrame(output)
