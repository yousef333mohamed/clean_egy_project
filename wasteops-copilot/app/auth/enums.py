"""Stable roles and permissions used by backend policy."""

from enum import StrEnum


class Role(StrEnum):
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    MANAGER = "MANAGER"
    DATA_ENGINEER = "DATA_ENGINEER"
    KNOWLEDGE_MANAGER = "KNOWLEDGE_MANAGER"
    PROMPT_ADMIN = "PROMPT_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    AUDITOR = "AUDITOR"


class Permission(StrEnum):
    DASHBOARD_READ = "dashboard:read"
    ANALYTICS_READ = "analytics:read"
    ASSISTANT_USE = "assistant:use"
    DECISIONS_REQUEST = "decisions:request"
    DECISIONS_PREVIEW = "decisions:preview"
    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_INGEST = "documents:ingest"
    DOCUMENTS_MANAGE = "documents:manage"
    DATASETS_READ = "datasets:read"
    DATASETS_VALIDATE = "datasets:validate"
    DATASETS_INGEST = "datasets:ingest"
    EVALUATIONS_READ = "evaluations:read"
    EVALUATIONS_RUN = "evaluations:run"
    TRACES_READ = "traces:read"
    FEEDBACK_CREATE = "feedback:create"
    FEEDBACK_READ = "feedback:read"
    PROMPTS_READ = "prompts:read"
    PROMPTS_CREATE = "prompts:create"
    PROMPTS_ACTIVATE = "prompts:activate"
    PROMPTS_ARCHIVE = "prompts:archive"
    USERS_READ = "users:read"
    AUDIT_READ = "audit:read"
    SYSTEM_CONFIGURE = "system:configure"
