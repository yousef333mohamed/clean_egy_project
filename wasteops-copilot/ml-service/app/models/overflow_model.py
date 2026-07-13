"""Calibratable overflow classifier with a transparent threshold baseline."""

import numpy as np
import pandas as pd
from typing import Any
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.models.base import ModelOutput, OperationalModel


class OverflowModel(OperationalModel):
    model_name = "bin-overflow"

    def __init__(self, version: str = "unregistered", threshold: float = 0.65, critical_fill_pct: float = 80) -> None:
        self.model_version = version
        self.feature_version = "1.0.0"
        self.decision_threshold = threshold
        self.critical_fill_pct = critical_fill_pct
        self.numeric = ["current_fill_level_pct", "fill_change_6h", "average_fill_rate_24h", "hours_since_last_collection"]
        self.categorical = ["region"]
        transformer = ColumnTransformer(
            [
                ("numeric", Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler())]), self.numeric),
                (
                    "categorical",
                    Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore"))]),
                    self.categorical,
                ),
            ]
        )
        self.estimator = Pipeline([("features", transformer), ("classifier", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))])
        self._fitted = False

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "OverflowModel":
        self.estimator.fit(features, target.astype(int))
        self._fitted = True
        return self

    def predict(self, features: pd.DataFrame) -> list[ModelOutput]:
        if self._fitted:
            probabilities = self.estimator.predict_proba(features)[:, 1]
            warning: list[str] = []
        else:
            fill = pd.to_numeric(features["current_fill_level_pct"], errors="coerce")
            probabilities = np.clip((fill.fillna(0).to_numpy() - (self.critical_fill_pct - 30)) / 30, 0, 1)
            warning = ["Fallback critical-fill baseline used; no approved fitted candidate was loaded."]
        output = []
        for position, probability in enumerate(probabilities):
            fill = float(features.iloc[position].get("current_fill_level_pct", 0) or 0)
            rate = float(features.iloc[position].get("fill_change_6h", 0) or 0)
            factors: list[dict[str, Any]] = [
                {"feature": "current_fill_level_pct", "direction": "increases_risk", "contribution": round(min(1.0, fill / 100), 4)},
                {
                    "feature": "fill_change_6h",
                    "direction": "increases_risk" if rate >= 0 else "decreases_risk",
                    "contribution": round(max(-1.0, min(1.0, rate / 30)), 4),
                },
            ]
            output.append(ModelOutput(float(probability), bool(probability >= self.decision_threshold), factors, list(warning)))
        return output
