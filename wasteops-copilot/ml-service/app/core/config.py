"""Validated settings for the private ML service."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ml_service_name: str = "WasteOps ML Service"
    ml_service_env: str = "development"
    ml_service_api_prefix: str = "/api"
    database_url: str = ""
    analytics_database_url: str = ""
    analytics_database_url_file: str = ""
    mlflow_tracking_uri: str = ""
    mlflow_experiment_prefix: str = "wasteops"
    model_artifact_directory: Path = Path("artifacts/models")
    model_refresh_interval_seconds: int = Field(default=300, ge=30)
    service_token: str = Field(default="", repr=False)
    admin_service_token: str = Field(default="", repr=False)
    service_token_file: str = ""
    admin_service_token_file: str = ""
    prediction_logging_enabled: bool = True
    drift_monitoring_enabled: bool = True
    model_explanations_enabled: bool = True
    min_training_rows: int = Field(default=100, ge=10)
    max_prediction_batch_size: int = Field(default=1000, ge=1, le=10000)
    prediction_timeout_seconds: float = Field(default=30, gt=0, le=120)
    critical_fill_threshold_pct: float = Field(default=80, gt=0, le=100)
    overflow_max_feature_age_minutes: int = Field(default=240, ge=1)
    truck_max_feature_age_hours: int = Field(default=48, ge=1)
    workforce_max_feature_age_hours: int = Field(default=24, ge=1)
    require_production_models: bool = False
    allowed_model_checksums: str = ""

    overflow_model_stage: str = "Production"
    collection_priority_model_stage: str = "Production"
    truck_anomaly_model_stage: str = "Production"
    missed_collection_model_stage: str = "Production"
    workforce_forecast_model_stage: str = "Production"

    @model_validator(mode="before")
    @classmethod
    def load_file_secrets(cls, values):
        if not isinstance(values, dict):
            return values
        output = dict(values)
        for target in ("analytics_database_url", "service_token", "admin_service_token"):
            source = output.get(f"{target}_file")
            if source and not output.get(target):
                path = Path(str(source))
                if not path.is_file():
                    raise ValueError(f"Secret file for {target} is unavailable")
                output[target] = path.read_text(encoding="utf-8").strip()
        return output

    @model_validator(mode="after")
    def production_guards(self) -> "Settings":
        if self.ml_service_env.casefold() == "production":
            if not self.service_token or not self.admin_service_token:
                raise ValueError("Production requires service and admin service tokens")
            if not self.analytics_database_url:
                raise ValueError("Production inference requires a read-only analytics database URL")
            if not self.allowed_model_checksums:
                raise ValueError("Production requires an artifact checksum allow-list")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
