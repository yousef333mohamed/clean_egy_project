"""Combined deterministic rules and Isolation Forest anomaly score."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from app.models.base import ModelOutput, OperationalModel


class TruckAnomalyModel(OperationalModel):
    model_name = "truck-anomaly"
    feature_version = "1.0.0"
    decision_threshold = 0.7
    columns = ["fuel_consumed_l", "distance_km", "fuel_efficiency_km_per_l", "load_kg", "trip_duration_min", "stops_completed"]

    def __init__(self, version: str = "unregistered") -> None:
        self.model_version = version
        self.estimator = Pipeline([("impute", SimpleImputer(strategy="median")), ("model", IsolationForest(contamination=0.05, random_state=42))])
        self._fitted = False

    def fit(self, features: pd.DataFrame, target: pd.Series | None = None) -> "TruckAnomalyModel":
        self.estimator.fit(features[self.columns])
        self._fitted = True
        return self

    def predict(self, features: pd.DataFrame) -> list[ModelOutput]:
        if self._fitted:
            raw = -self.estimator.decision_function(features[self.columns])
            scores = 1 / (1 + np.exp(-5 * raw))
            fallback = []
        else:
            efficiency = pd.to_numeric(features["fuel_efficiency_km_per_l"], errors="coerce")
            median = efficiency.median()
            mad = (efficiency - median).abs().median() or 1.0
            scores = np.clip((efficiency - median).abs().fillna(0).to_numpy() / (6 * mad), 0, 1)
            fallback = ["Robust-deviation baseline used; no approved fitted candidate was loaded."]
        return [
            ModelOutput(
                float(score),
                bool(score >= self.decision_threshold),
                [{"feature": "trip_behavior_deviation", "direction": "increases_risk", "contribution": round(float(score), 4)}],
                fallback + ["An anomaly requires review and does not remove a truck from service."],
            )
            for score in scores
        ]
