import pandas as pd
import joblib
from app.models.collection_priority_model import CollectionPriorityModel
from app.models.overflow_model import OverflowModel
from app.models.truck_anomaly_model import TruckAnomalyModel
from app.models.workforce_forecast_model import WorkforceForecastModel


def test_overflow_baseline_returns_bounded_probability():
    frame = pd.DataFrame({"current_fill_level_pct": [40, 95], "fill_change_6h": [1, 15]})
    values = OverflowModel().predict(frame)
    assert all(0 <= item.value <= 1 for item in values)
    assert any("baseline" in warning.casefold() for warning in values[0].warnings)


def test_priority_is_transparent_and_non_executing():
    frame = pd.DataFrame([{"overflow_probability": 0.9, "current_urgency": 0.9, "service_history": 0.5, "operational_context": 0.5, "sensor_reliability": 1}])
    output = CollectionPriorityModel().predict(frame)[0]
    assert 0 <= output.value <= 1
    assert any("does not dispatch" in warning for warning in output.warnings)


def test_truck_anomaly_does_not_remove_vehicle():
    frame = pd.DataFrame({"fuel_efficiency_km_per_l": [1, 5, 6]})
    output = TruckAnomalyModel().predict(frame)[0]
    assert any("does not remove" in warning for warning in output.warnings)


def test_workforce_is_non_disciplinary():
    frame = pd.DataFrame({"recent_required_workers_28d": [14]})
    output = WorkforceForecastModel().predict(frame)[0]
    assert output.value == 14
    assert any("disciplinary" in warning for warning in output.warnings)


def test_overflow_candidate_training_and_serialization(tmp_path):
    frame = pd.DataFrame(
        {
            "current_fill_level_pct": [30 + index for index in range(60)],
            "fill_change_6h": [index % 12 for index in range(60)],
            "average_fill_rate_24h": [0.5 + index / 100 for index in range(60)],
            "hours_since_last_collection": [index * 2 for index in range(60)],
            "region": ["Cairo" if index % 2 else "Delta" for index in range(60)],
        }
    )
    target = frame["current_fill_level_pct"] >= 65
    model = OverflowModel(version="smoke").fit(frame, target)
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    loaded = joblib.load(path)
    predictions = loaded.predict(frame.iloc[-2:])
    assert path.is_file() and all(0 <= item.value <= 1 for item in predictions)
