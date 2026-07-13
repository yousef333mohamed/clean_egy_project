"""Audit event categories."""

from enum import StrEnum


class AuditAction(StrEnum):
    AUTHENTICATION_FAILURE = "authentication.failure"
    AUTHORIZATION_DENIAL = "authorization.denial"
    ADMINISTRATIVE_CHANGE = "administrative.change"
    PROMPT_CHANGE = "prompt.change"
    INGESTION = "ingestion"
    EVALUATION = "evaluation"
    JOB_CANCEL = "job.cancel"
