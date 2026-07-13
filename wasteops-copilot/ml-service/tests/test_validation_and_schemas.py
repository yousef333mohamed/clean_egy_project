from datetime import timedelta
import pytest
from pydantic import ValidationError
from app.inference.prediction_validator import PredictionValidationError, freshness, validate_batch
from app.schemas.overflow import OverflowPrediction


def test_batch_limit_and_supported_probability(as_of):
    with pytest.raises(PredictionValidationError):
        validate_batch(["a", "b"], 1)
    with pytest.raises(ValidationError):
        OverflowPrediction(
            bin_id="B",
            horizon_hours=24,
            overflow_probability=1.2,
            predicted_class=True,
            decision_threshold=0.6,
            risk_level="HIGH",
            model_name="m",
            model_version="1",
            prediction_timestamp=as_of,
            feature_timestamp=as_of,
            data_age_seconds=0,
        )


def test_stale_features_are_labeled_or_rejected(as_of):
    timestamp = as_of - timedelta(hours=10)
    age, warnings = freshness(timestamp, as_of, 60, degraded_allowed=True)
    assert age > 60 and warnings
    with pytest.raises(PredictionValidationError):
        freshness(timestamp, as_of, 60)


def test_future_feature_timestamp_rejected(as_of):
    with pytest.raises(PredictionValidationError):
        freshness(as_of + timedelta(seconds=1), as_of, 60)
