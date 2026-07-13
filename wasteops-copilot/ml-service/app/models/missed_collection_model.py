"""Missed-collection probability baseline and logistic candidate."""

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from app.models.base import ModelOutput, OperationalModel


class MissedCollectionModel(OperationalModel):
    model_name = "missed-collection"
    feature_version = "1.0.0"
    decision_threshold = 0.6
    columns = ["historical_missed_rate_28d", "emergency_requests", "complaints", "critical_bin_count", "available_trucks", "attendance_rate"]

    def __init__(self, version: str = "unregistered") -> None:
        self.model_version = version
        self.estimator = Pipeline(
            [
                ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                ("scale", StandardScaler()),
                ("model", LogisticRegression(class_weight="balanced", random_state=42)),
            ]
        )
        self._fitted = False

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "MissedCollectionModel":
        self.estimator.fit(features[self.columns], target.astype(int))
        self._fitted = True
        return self

    def predict(self, features: pd.DataFrame) -> list[ModelOutput]:
        if self._fitted:
            values = self.estimator.predict_proba(features[self.columns])[:, 1]
            warnings = []
        else:
            values = np.clip(pd.to_numeric(features["historical_missed_rate_28d"], errors="coerce").fillna(0.5).to_numpy(), 0, 1)
            warnings = ["Historical regional-rate baseline used; no approved fitted candidate was loaded."]
        return [
            ModelOutput(
                float(value),
                value >= self.decision_threshold,
                [{"feature": "historical_missed_rate_28d", "direction": "increases_risk", "contribution": round(float(value), 4)}],
                list(warnings),
            )
            for value in values
        ]
