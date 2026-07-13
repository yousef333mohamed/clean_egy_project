"""Evaluation lifecycle enums."""

from enum import StrEnum


class EvaluationMode(StrEnum):
    FAKE_PROVIDERS = "FAKE_PROVIDERS"
    RECORDED_RESPONSES = "RECORDED_RESPONSES"
    LIVE_PROVIDERS = "LIVE_PROVIDERS"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
