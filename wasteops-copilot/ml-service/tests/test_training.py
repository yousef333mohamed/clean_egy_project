from datetime import datetime, timedelta, timezone
import pandas as pd
import pytest
from training.datasets import assert_features_available_before, dataset_version, overflow_targets
from training.splits import assert_no_temporal_overlap, chronological_split


def test_chronological_split_has_no_overlap():
    frame = pd.DataFrame({"timestamp": pd.date_range("2026-01-01", periods=30, tz="UTC"), "value": range(30)})
    split = chronological_split(frame, "timestamp")
    assert_no_temporal_overlap(split, "timestamp")
    assert split.train.timestamp.max() < split.validation.timestamp.min() < split.test.timestamp.min()


def test_dataset_version_is_order_stable():
    frame = pd.DataFrame({"a": [2, 1], "b": ["y", "x"]})
    assert dataset_version(frame) == dataset_version(frame.iloc[::-1])


def test_overflow_target_uses_only_selected_future_horizon():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    frame = pd.DataFrame({"bin_id": ["B"] * 3, "timestamp": [now, now + timedelta(hours=5), now + timedelta(hours=8)], "fill_level_pct": [50, 85, 90]})
    target = overflow_targets(frame, 6, 80)
    assert bool(target.iloc[0]) is True


def test_availability_leakage_rejected():
    frame = pd.DataFrame({"feature": ["2026-01-02T00:00:00Z"], "prediction": ["2026-01-01T00:00:00Z"]})
    with pytest.raises(ValueError, match="leakage"):
        assert_features_available_before(frame, "feature", "prediction")
