"""Non-disciplinary workforce requirement regression baseline."""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from app.models.base import ModelOutput, OperationalModel


class WorkforceForecastModel(OperationalModel):
    model_name = "workforce-forecast"
    feature_version = "1.0.0"
    decision_threshold = 0.0
    columns = ["expected_workload", "historical_task_volume", "attendance_rate", "critical_bin_volume", "truck_trips"]

    def __init__(self, version: str = "unregistered") -> None:
        self.model_version = version
        self.estimator = Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)), ("model", HistGradientBoostingRegressor(random_state=42))])
        self._fitted = False

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "WorkforceForecastModel":
        self.estimator.fit(features[self.columns], target)
        self._fitted = True
        return self

    def predict(self, features: pd.DataFrame) -> list[ModelOutput]:
        if self._fitted:
            values = self.estimator.predict(features[self.columns])
            warnings = []
        else:
            values = pd.to_numeric(features["recent_required_workers_28d"], errors="coerce").fillna(0).to_numpy()
            warnings = ["Recent rolling-average baseline used; no approved fitted candidate was loaded."]
        return [
            ModelOutput(
                float(max(0, value)),
                None,
                [{"feature": "recent_required_workers_28d", "direction": "increases_forecast", "contribution": round(float(np.clip(value / 100, 0, 1)), 4)}],
                list(warnings) + ["Forecast is for staffing review only and must not support disciplinary decisions or automatic assignment."],
            )
            for value in values
        ]
