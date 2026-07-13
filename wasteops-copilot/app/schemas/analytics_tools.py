"""Allow-listed analytics tool parameters and result contracts."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.analytics.enums import SortDirection
from app.utils.safe_identifiers import validate_safe_value


class AnalyticsToolParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    latest_available: bool = False
    region: str | None = None
    governorate: str | None = None
    bin_id: str | None = None
    truck_id: str | None = None
    worker_id: str | None = None
    shift: str | None = None
    waste_type: str | None = None
    sensor_status: str | None = None
    trip_status: str | None = None
    traffic_level: str | None = None
    holiday: bool | None = None
    festival: bool | None = None
    weekend: bool | None = None
    group_by: str | None = None
    metric: str | None = None
    sort_direction: SortDirection = SortDirection.DESC
    limit: int | None = Field(default=None, gt=0)

    @field_validator("region", "governorate", "bin_id", "truck_id", "worker_id", "shift", "waste_type", "sensor_status", "trip_status", "traffic_level")
    @classmethod
    def safe_filter(cls, value: str | None) -> str | None:
        return validate_safe_value(value) if value is not None else None

    @field_validator("group_by", "metric")
    @classmethod
    def registry_token(cls, value: str | None) -> str | None:
        if value is not None and not value.replace("_", "").isalnum():
            raise ValueError("must be a registry identifier")
        return value

    @model_validator(mode="after")
    def ordered_ranges(self) -> "AnalyticsToolParameters":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        if self.start_timestamp and self.end_timestamp and self.start_timestamp > self.end_timestamp:
            raise ValueError("start_timestamp must not be after end_timestamp")
        return self


class AnalyticsToolRequest(BaseModel):
    parameters: AnalyticsToolParameters = Field(default_factory=AnalyticsToolParameters)


class AnalyticsToolResult(BaseModel):
    tool_name: str
    metric: str | None = None
    description: str
    columns: list[str]
    rows: list[dict[str, Any]]
    filters: dict[str, Any]
    data_period_start: date | datetime | None = None
    data_period_end: date | datetime | None = None
    notes: list[str] = Field(default_factory=list)
    aggregation_definitions: dict[str, str] = Field(default_factory=dict)
