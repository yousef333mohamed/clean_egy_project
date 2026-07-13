"""Domain exceptions."""


class WasteOpsError(Exception):
    """Base application exception."""


class IngestionError(WasteOpsError):
    """Raised for ingestion failures."""


class UnsafeQueryError(WasteOpsError):
    """Raised when generated SQL violates safety policy."""


class ExternalServiceError(WasteOpsError):
    """Raised when an LLM or embedding provider fails."""
