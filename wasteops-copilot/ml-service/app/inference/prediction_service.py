"""Model-owned prediction orchestration; no operational actions are performed."""

from datetime import datetime
from math import ceil
from typing import Literal

import pandas as pd

from app.inference.explanation_service import safe_factors
from app.inference.prediction_validator import PredictionValidationError, freshness, validate_batch
from app.models.collection_priority_model import CollectionPriorityModel
from app.models.missed_collection_model import MissedCollectionModel
from app.models.overflow_model import OverflowModel
from app.models.truck_anomaly_model import TruckAnomalyModel
from app.models.workforce_forecast_model import WorkforceForecastModel
from app.schemas.collection_priority import CollectionPriorityPrediction, PriorityComponents
from app.schemas.missed_collection import MissedCollectionPrediction
from app.schemas.overflow import OverflowPrediction
from app.schemas.truck_anomaly import TruckAnomalyPrediction
from app.schemas.workforce_forecast import PredictionInterval, WorkforceForecast


Horizon = Literal[6, 12, 24]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def risk_level(value: float) -> RiskLevel:
    return "CRITICAL" if value >= 0.9 else "HIGH" if value >= 0.7 else "MEDIUM" if value >= 0.4 else "LOW"


class PredictionService:
    def __init__(self, repository, settings) -> None:
        self.repository = repository
        self.settings = settings
        self.overflow_model = OverflowModel(critical_fill_pct=settings.critical_fill_threshold_pct)
        self.priority_model = CollectionPriorityModel()
        self.truck_model = TruckAnomalyModel()
        self.missed_model = MissedCollectionModel()
        self.workforce_model = WorkforceForecastModel()

    def overflow(self, bin_ids: list[str], horizon: Horizon, as_of: datetime) -> list[OverflowPrediction]:
        ids = validate_batch(bin_ids, self.settings.max_prediction_batch_size)
        frame = self.repository.bins(ids, as_of)
        self._ensure_all(ids, frame, "bin_id")
        outputs = self.overflow_model.predict(frame)
        result = []
        for (_, row), output in zip(frame.iterrows(), outputs, strict=True):
            timestamp = pd.Timestamp(row["feature_timestamp"]).to_pydatetime()
            age, warnings = freshness(timestamp, as_of, self.settings.overflow_max_feature_age_minutes * 60, degraded_allowed=True)
            result.append(
                OverflowPrediction(
                    bin_id=row["bin_id"],
                    horizon_hours=horizon,
                    overflow_probability=output.value,
                    predicted_class=bool(output.predicted_class),
                    decision_threshold=self.overflow_model.decision_threshold,
                    risk_level=risk_level(output.value),
                    model_name=self.overflow_model.model_name,
                    model_version=self.overflow_model.model_version,
                    prediction_timestamp=as_of,
                    feature_timestamp=timestamp,
                    data_age_seconds=age,
                    top_factors=safe_factors(output.factors),
                    warnings=warnings + output.warnings,
                )
            )
        return result

    def priority(self, bin_ids: list[str], horizon: Horizon, as_of: datetime) -> list[CollectionPriorityPrediction]:
        overflow = self.overflow(bin_ids, horizon, as_of)
        frame = self.repository.bins(bin_ids, as_of).set_index("bin_id")
        scoring = pd.DataFrame(
            [
                {
                    "overflow_probability": item.overflow_probability,
                    "current_urgency": float(frame.loc[item.bin_id, "current_fill_level_pct"]) / 100,
                    "service_history": min(1, float(frame.loc[item.bin_id, "hours_since_last_collection"] or 0) / 168),
                    "operational_context": 0.5,
                    "sensor_reliability": 0.0 if bool(frame.loc[item.bin_id, "sensor_fault_flag"]) else 1.0,
                }
                for item in overflow
            ]
        )
        outputs = self.priority_model.predict(scoring)
        result = []
        for base, (_, parts), output in zip(overflow, scoring.iterrows(), outputs, strict=True):
            components = PriorityComponents(
                overflow_risk=parts.overflow_probability,
                current_urgency=parts.current_urgency,
                service_history=parts.service_history,
                operational_context=parts.operational_context,
                sensor_reliability=parts.sensor_reliability,
            )
            result.append(
                CollectionPriorityPrediction(
                    bin_id=base.bin_id,
                    priority_score=output.value,
                    priority_level=risk_level(output.value),
                    overflow_probability=base.overflow_probability,
                    recommended_review_window_hours=6 if output.value >= 0.7 else 12 if output.value >= 0.4 else 24,
                    score_components=components,
                    model_name=self.priority_model.model_name,
                    model_version=self.priority_model.model_version,
                    prediction_timestamp=as_of,
                    feature_timestamp=base.feature_timestamp,
                    data_age_seconds=base.data_age_seconds,
                    top_factors=safe_factors(output.factors),
                    warnings=list(dict.fromkeys(base.warnings + output.warnings)),
                )
            )
        return result

    def truck_anomalies(self, truck_ids: list[str], as_of: datetime) -> list[TruckAnomalyPrediction]:
        ids = validate_batch(truck_ids, self.settings.max_prediction_batch_size)
        frame = self.repository.trucks(ids, as_of)
        self._ensure_all(ids, frame, "truck_id")
        outputs = self.truck_model.predict(frame)
        result = []
        for (_, row), output in zip(frame.iterrows(), outputs, strict=True):
            timestamp = pd.Timestamp(row.feature_timestamp).to_pydatetime()
            age, warnings = freshness(timestamp, as_of, self.settings.truck_max_feature_age_hours * 3600, degraded_allowed=True)
            rules = []
            if float(row.fuel_consumed_l) < 0 or float(row.trip_duration_min) < 0:
                rules.append("invalid_negative_measurement")
            result.append(
                TruckAnomalyPrediction(
                    truck_id=row.truck_id,
                    trip_date=row.trip_date,
                    is_anomalous=bool(output.predicted_class or rules),
                    anomaly_score=output.value,
                    severity=risk_level(output.value),
                    triggered_rules=rules,
                    model_factors=safe_factors(output.factors),
                    model_name=self.truck_model.model_name,
                    model_version=self.truck_model.model_version,
                    prediction_timestamp=as_of,
                    feature_timestamp=timestamp,
                    data_age_seconds=age,
                    warnings=warnings + output.warnings,
                )
            )
        return result

    def missed(self, scope_ids: list[str], scope_type: str, horizon: Horizon, as_of: datetime) -> list[MissedCollectionPrediction]:
        ids = validate_batch(scope_ids, self.settings.max_prediction_batch_size)
        if scope_type != "region":
            raise PredictionValidationError("Only region scope is currently supported")
        frame = self.repository.missed_collections(ids, as_of)
        self._ensure_all(ids, frame, "region")
        outputs = self.missed_model.predict(frame)
        result = []
        for (_, row), output in zip(frame.iterrows(), outputs, strict=True):
            timestamp = pd.Timestamp(row.feature_timestamp).to_pydatetime()
            age, warnings = freshness(timestamp, as_of, 48 * 3600, degraded_allowed=True)
            result.append(
                MissedCollectionPrediction(
                    scope_type="region",
                    scope_id=row.region,
                    horizon_hours=horizon,
                    missed_collection_probability=output.value,
                    risk_level=risk_level(output.value),
                    model_name=self.missed_model.model_name,
                    model_version=self.missed_model.model_version,
                    prediction_timestamp=as_of,
                    feature_timestamp=timestamp,
                    data_age_seconds=age,
                    top_factors=safe_factors(output.factors),
                    warnings=warnings + output.warnings,
                )
            )
        return result

    def workforce(self, regions: list[str], shifts: list[str], forecast_date, as_of: datetime) -> list[WorkforceForecast]:
        validate_batch(regions, self.settings.max_prediction_batch_size)
        validate_batch(shifts, 20)
        frame = self.repository.workforce(regions, shifts, forecast_date, as_of)
        expected = {(region, shift) for region in regions for shift in shifts}
        found = set(zip(frame.get("region", []), frame.get("shift", [])))
        if expected - found:
            raise PredictionValidationError(f"Unsupported or data-deficient region/shift pairs: {sorted(expected - found)}")
        outputs = self.workforce_model.predict(frame)
        result = []
        for (_, row), output in zip(frame.iterrows(), outputs, strict=True):
            timestamp = pd.Timestamp(row.feature_timestamp).to_pydatetime()
            age, warnings = freshness(timestamp, as_of, self.settings.workforce_max_feature_age_hours * 3600, degraded_allowed=True)
            required = max(0, ceil(output.value))
            margin = max(1, ceil(required * 0.2))
            result.append(
                WorkforceForecast(
                    region=row.region,
                    shift=row.shift,
                    forecast_date=forecast_date,
                    required_workers=required,
                    prediction_interval=PredictionInterval(lower=max(0, required - margin), upper=required + margin),
                    model_name=self.workforce_model.model_name,
                    model_version=self.workforce_model.model_version,
                    prediction_timestamp=as_of,
                    feature_timestamp=timestamp,
                    data_age_seconds=age,
                    top_factors=safe_factors(output.factors),
                    warnings=warnings + output.warnings,
                )
            )
        return result

    @staticmethod
    def _ensure_all(expected: list[str], frame: pd.DataFrame, column: str) -> None:
        if frame.empty:
            raise PredictionValidationError("No point-in-time features are available for the requested assets")
        missing = set(expected) - set(frame[column].astype(str))
        if missing:
            raise PredictionValidationError(f"Unknown or data-deficient assets: {sorted(missing)}")
