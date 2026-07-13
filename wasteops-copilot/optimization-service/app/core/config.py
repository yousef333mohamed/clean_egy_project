from functools import lru_cache
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "WasteOps Optimization Service"
    environment: str = "development"
    service_token: str = Field(default="", repr=False)
    service_token_file: str = ""
    max_bins: int = Field(default=500, ge=1, le=2000)
    max_trucks: int = Field(default=100, ge=1, le=500)
    solve_timeout_seconds: int = Field(default=10, ge=1, le=60)
    max_alternative_plans: int = Field(default=2, ge=0, le=5)

    @model_validator(mode="before")
    @classmethod
    def secrets(cls, values):
        if isinstance(values, dict) and values.get("service_token_file") and not values.get("service_token"):
            path = Path(values["service_token_file"])
            if not path.is_file():
                raise ValueError("Service token file unavailable")
            values = dict(values)
            values["service_token"] = path.read_text(encoding="utf-8").strip()
        return values

    @model_validator(mode="after")
    def production(self):
        if self.environment.casefold() == "production" and not self.service_token:
            raise ValueError("Production service token required")
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()
