from datetime import timedelta
import pandas as pd
import pytest
from app.features.bin_features import build_bin_features
from app.features.feature_registry import FEATURES, definitions_for
from app.features.feature_validation import enforce_point_in_time, validate_feature_frame


def test_registry_contains_leakage_and_availability_metadata():
    assert FEATURES and all(item.availability_delay and item.leakage_risk for item in FEATURES)
    assert definitions_for("bin-overflow")


def test_bin_features_use_only_prior_readings(bin_readings, as_of):
    result = build_bin_features(bin_readings, as_of)
    assert set(result.bin_id) == {"BIN-1", "BIN-2"}
    assert result["fill_change_6h"].notna().all()


def test_future_feature_rejected(bin_readings, as_of):
    future = bin_readings.iloc[[0]].copy()
    future["reading_timestamp"] = as_of + timedelta(minutes=1)
    with pytest.raises(ValueError, match="Temporal leakage"):
        enforce_point_in_time(future, "reading_timestamp", as_of)


def test_missing_values_get_indicators_not_zero(as_of):
    frame = pd.DataFrame({"current_fill_level_pct": [55.0], "sensor_fault_flag": [False], "region": ["Cairo"]})
    result = validate_feature_frame(frame, "bin-overflow", as_of)
    assert pd.isna(result.frame.loc[0, "fill_change_6h"])
    assert result.frame.loc[0, "fill_change_6h__missing"] == 1
