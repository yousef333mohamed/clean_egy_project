"""Prompt validation and immutable-content helpers."""

import re

from app.models.prompt_version import PromptVersion

PROMPT_KEYS = frozenset(
    {
        "rag_system",
        "rag_answer",
        "query_rewrite",
        "analytics_router",
        "analytics_answer",
        "hybrid_answer",
        "decision_router",
        "candidate_actions",
        "decision_explanation",
    }
)
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
CREDENTIAL_PATTERN = re.compile(r"(?i)(?:api[_-]?key|password|secret|authorization)\s*[:=]\s*(?!\{|\[|<|REDACTED)[\"']?[A-Za-z0-9_./+\-=]{8,}")


def validate_prompt_key(prompt_key: str) -> str:
    if prompt_key not in PROMPT_KEYS:
        raise ValueError(f"Unsupported prompt key: {prompt_key}")
    return prompt_key


def validate_prompt_content(content: str) -> str:
    normalized = content.strip()
    if not normalized:
        raise ValueError("Prompt content must not be empty")
    if len(normalized) > 100_000:
        raise ValueError("Prompt content exceeds 100000 characters")
    if CREDENTIAL_PATTERN.search(normalized):
        raise ValueError("Prompt content appears to contain credentials")
    return normalized


def validate_version(version: str) -> str:
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError("Prompt version must use semantic versioning")
    return version


def content_hash(content: str) -> str:
    return PromptVersion.hash_content(validate_prompt_content(content))
