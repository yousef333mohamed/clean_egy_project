"""Common versioned model contract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ModelOutput:
    value: float
    predicted_class: bool | None
    factors: list[dict[str, Any]]
    warnings: list[str]


class OperationalModel(ABC):
    model_name: str
    model_version: str
    feature_version: str
    decision_threshold: float

    @abstractmethod
    def fit(self, features: pd.DataFrame, target: pd.Series) -> "OperationalModel": ...

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> list[ModelOutput]: ...
