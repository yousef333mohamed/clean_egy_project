"""Transparent hybrid collection-priority score; never an execution command."""

import pandas as pd
from app.models.base import ModelOutput, OperationalModel


class CollectionPriorityModel(OperationalModel):
    model_name = "collection-priority"
    model_version = "rules-1"
    feature_version = "1.0.0"
    decision_threshold = 0.7
    weights = {"overflow_probability": 0.40, "current_urgency": 0.25, "service_history": 0.15, "operational_context": 0.10, "sensor_reliability": 0.10}

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "CollectionPriorityModel":
        return self

    def predict(self, features: pd.DataFrame) -> list[ModelOutput]:
        outputs = []
        for _, row in features.iterrows():
            parts = {name: max(0.0, min(1.0, float(row.get(name, 0.5) if pd.notna(row.get(name, 0.5)) else 0.5))) for name in self.weights}
            score = sum(parts[name] * weight for name, weight in self.weights.items())
            factors = [{"feature": name, "direction": "increases_risk", "contribution": round(parts[name] * self.weights[name], 4)} for name in self.weights]
            outputs.append(
                ModelOutput(
                    score, score >= self.decision_threshold, factors[:5], ["Priority is advisory and requires manager review; it does not dispatch a truck."]
                )
            )
        return outputs
