"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Any
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables or .env."""

    app_name: str = "WasteOps Decision Intelligence Copilot"
    app_environment: str = "development"
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_allow_credentials: bool = True
    trusted_hosts: str = "localhost,127.0.0.1,testserver,test"
    auth_enabled: bool = False
    auth_provider: str = "oidc"
    oidc_issuer_url: str = ""
    oidc_jwks_url: str = ""
    oidc_audience: str = "wasteops-api"
    oidc_client_id: str = ""
    oidc_role_claim: str = "roles"
    oidc_permission_claim: str = "permissions"
    jwt_allowed_algorithms: str = "RS256"
    jwt_clock_skew_seconds: int = Field(default=60, ge=0, le=300)
    jwks_cache_ttl_seconds: int = Field(default=3600, ge=60)
    jwks_request_timeout_seconds: float = Field(default=10, gt=0, le=30)
    allow_development_auth: bool = False
    development_auth_user_id: str = "dev-user"
    development_auth_roles: str = "SYSTEM_ADMIN"
    max_request_body_bytes: int = Field(default=10_485_760, ge=1024)
    redis_url: str = Field(default="redis://localhost:6379/0", repr=False)
    redis_required: bool = False
    rate_limit_enabled: bool = False
    rate_limit_default_per_minute: int = Field(default=120, ge=1)
    rate_limit_expensive_per_minute: int = Field(default=20, ge=1)
    rate_limit_admin_per_minute: int = Field(default=30, ge=1)
    rate_limit_key_prefix: str = "wasteops:rate"
    metrics_token: str = Field(default="", repr=False)
    app_release_version: str = "0.1.0"
    app_commit_sha: str = "unknown"
    app_build_time: str = "unknown"
    object_storage_backend: str = "local"
    object_storage_directory: str = "data/storage"
    object_storage_bucket: str = ""
    object_storage_endpoint_url: str = ""
    object_storage_region: str = ""
    background_jobs_enabled: bool = False
    evaluation_result_retention_days: int = Field(default=365, ge=1)
    audit_log_retention_days: int = Field(default=730, ge=1)
    feedback_retention_days: int = Field(default=365, ge=1)
    failed_job_retention_days: int = Field(default=90, ge=1)
    database_url: str = ""
    database_sync_url: str = ""
    database_url_file: str = ""
    database_sync_url_file: str = ""
    redis_url_file: str = ""
    llm_api_key_file: str = ""
    metrics_token_file: str = ""
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)
    llm_api_key: str = Field(default="", repr=False)
    llm_base_url: str = "https://api.openai.com/v1"
    chat_model_name: str = "gpt-4.1-mini"
    embedding_model_name: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("EMBEDDING_MODEL", "EMBEDDING_MODEL_NAME"),
    )
    vector_dimensions: int = Field(default=1536, ge=1, validation_alias=AliasChoices("EMBEDDING_DIMENSIONS", "VECTOR_DIMENSIONS"))
    retrieval_top_k: int = Field(default=8, ge=1, le=100)
    retrieval_candidate_limit: int = Field(default=30, ge=1, le=500)
    retrieval_min_score: float = Field(default=0.45, ge=0, le=1)
    retrieval_vector_weight: float = Field(default=0.75, ge=0, le=1)
    retrieval_keyword_weight: float = Field(default=0.25, ge=0, le=1)
    retrieval_max_context_tokens: int = Field(default=5000, gt=0)
    retrieval_max_chunks_per_document: int = Field(default=3, gt=0)
    retrieval_max_query_chars: int = Field(default=4000, gt=0)
    retrieval_enable_query_rewrite: bool = True
    retrieval_enable_hybrid: bool = True
    retrieval_enable_reranking: bool = True
    retrieval_allow_production_content: bool = False
    llm_temperature: float = Field(default=0.1, ge=0, le=2)
    llm_max_output_tokens: int = Field(default=1200, gt=0)
    llm_timeout_seconds: float = Field(default=90, gt=0)
    llm_max_retries: int = Field(default=3, ge=0)
    enable_chat_api: bool = True
    enable_retrieval_debug_api: bool = True
    sql_query_timeout_ms: int = Field(default=5000, ge=100)
    sql_row_limit: int = Field(default=200, ge=1, le=5000)
    csv_batch_size: int = Field(default=5000, ge=1)
    source_timezone: str = "Africa/Cairo"
    ingestion_strict_columns: bool = False
    enable_ingestion_api: bool = True
    data_dir: str = "data"
    documents_directory: str = "data/documents"
    document_chunk_size: int = Field(default=700, gt=0)
    document_chunk_overlap: int = Field(default=120, ge=0)
    document_min_chunk_size: int = Field(default=80, gt=0)
    document_max_file_size_mb: int = Field(default=25, gt=0)
    document_metadata_strict: bool = False
    embedding_batch_size: int = Field(default=50, gt=0)
    embedding_max_retries: int = Field(default=3, ge=0)
    embedding_timeout_seconds: float = Field(default=60, gt=0)
    enable_document_ingestion_api: bool = True
    analytics_default_limit: int = Field(default=50, gt=0)
    analytics_max_limit: int = Field(default=200, gt=0)
    analytics_query_timeout_seconds: int = Field(default=15, gt=0)
    analytics_max_date_range_days: int = Field(default=366, gt=0)
    analytics_allow_raw_sql: bool = False
    analytics_enable_debug_api: bool = True
    analytics_enable_explain: bool = False
    enable_analytics_api: bool = True
    enable_hybrid_chat_api: bool = True
    truck_fuel_anomaly_multiplier: float = Field(default=1.5, gt=1)
    truck_duration_anomaly_multiplier: float = Field(default=1.5, gt=1)
    enable_decision_api: bool = True
    enable_decision_debug_api: bool = True
    decision_max_options: int = Field(default=4, ge=2, le=10)
    decision_min_evidence_items: int = Field(default=2, gt=0)
    decision_min_confidence: float = Field(default=0.45, ge=0, le=1)
    decision_require_document_guidance: bool = False
    decision_require_human_approval: bool = True
    decision_service_impact_weight: float = Field(default=0.30, ge=0, le=1)
    decision_urgency_weight: float = Field(default=0.25, ge=0, le=1)
    decision_risk_weight: float = Field(default=0.20, ge=0, le=1)
    decision_feasibility_weight: float = Field(default=0.15, ge=0, le=1)
    decision_policy_alignment_weight: float = Field(default=0.10, ge=0, le=1)
    confidence_retrieval_coverage_weight: float = Field(default=0.25, ge=0, le=1)
    confidence_source_quality_weight: float = Field(default=0.20, ge=0, le=1)
    confidence_data_completeness_weight: float = Field(default=0.15, ge=0, le=1)
    confidence_source_agreement_weight: float = Field(default=0.15, ge=0, le=1)
    confidence_recency_weight: float = Field(default=0.10, ge=0, le=1)
    confidence_model_reliability_weight: float = Field(default=0.15, ge=0, le=1)
    data_science_provider: str = "disabled"
    allow_mock_data_science: bool = False
    ml_service_base_url: str = "http://ml_service:8001"
    ml_service_token: str = Field(default="", repr=False)
    ml_service_token_file: str = ""
    ml_admin_service_token: str = Field(default="", repr=False)
    ml_admin_service_token_file: str = ""
    ml_client_timeout_seconds: float = Field(default=30, gt=0, le=120)
    ml_client_max_retries: int = Field(default=2, ge=0, le=5)
    ml_circuit_breaker_failure_threshold: int = Field(default=5, ge=1, le=20)
    ml_circuit_breaker_recovery_seconds: float = Field(default=60, gt=0, le=600)
    enable_evaluation_api: bool = True
    enable_prompt_admin_api: bool = True
    enable_trace_api: bool = True
    enable_feedback_api: bool = True
    tracing_enabled: bool = True
    trace_store_inputs: bool = False
    trace_store_outputs: bool = False
    trace_retention_days: int = Field(default=30, ge=1)
    evaluation_max_concurrency: int = Field(default=4, ge=1, le=32)
    evaluation_timeout_seconds: float = Field(default=120, gt=0)
    evaluation_allow_live_providers: bool = False
    quality_gate_min_retrieval_recall: float = Field(default=0.80, ge=0, le=1)
    quality_gate_min_citation_validity: float = Field(default=0.95, ge=0, le=1)
    quality_gate_min_route_accuracy: float = Field(default=0.90, ge=0, le=1)
    quality_gate_min_tool_accuracy: float = Field(default=0.90, ge=0, le=1)
    quality_gate_min_groundedness: float = Field(default=0.90, ge=0, le=1)
    quality_gate_max_numeric_error_rate: float = Field(default=0.00, ge=0, le=1)
    quality_gate_max_critical_failures: int = Field(default=0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def load_file_secrets(cls, values: Any) -> Any:
        """Resolve explicitly supported Docker/Kubernetes secret files."""
        if not isinstance(values, dict):
            return values
        output = dict(values)
        for target in ("database_url", "database_sync_url", "redis_url", "llm_api_key", "metrics_token", "ml_service_token", "ml_admin_service_token"):
            file_value = output.get(f"{target}_file")
            if file_value and not output.get(target):
                path = Path(str(file_value))
                if not path.is_file():
                    raise ValueError(f"Secret file for {target} is unavailable")
                output[target] = path.read_text(encoding="utf-8").strip()
        return output

    @field_validator("cors_allowed_origins", "trusted_hosts")
    @classmethod
    def reject_wildcards(cls, value: str) -> str:
        """Reject wildcard transport trust, which is unsafe with credentials."""
        if "*" in {part.strip() for part in value.split(",")}:
            raise ValueError("wildcards are not allowed")
        return value

    @model_validator(mode="after")
    def validate_document_chunking(self) -> "Settings":
        """Reject chunk settings that cannot produce controlled overlap."""
        if self.document_chunk_overlap >= self.document_chunk_size:
            raise ValueError("DOCUMENT_CHUNK_OVERLAP must be smaller than DOCUMENT_CHUNK_SIZE")
        if self.document_min_chunk_size > self.document_chunk_size:
            raise ValueError("DOCUMENT_MIN_CHUNK_SIZE must not exceed DOCUMENT_CHUNK_SIZE")
        if self.retrieval_candidate_limit < self.retrieval_top_k:
            raise ValueError("RETRIEVAL_CANDIDATE_LIMIT must be greater than or equal to RETRIEVAL_TOP_K")
        if abs((self.retrieval_vector_weight + self.retrieval_keyword_weight) - 1.0) > 0.001:
            raise ValueError("RETRIEVAL_VECTOR_WEIGHT and RETRIEVAL_KEYWORD_WEIGHT must add up to 1")
        if self.analytics_max_limit < self.analytics_default_limit:
            raise ValueError("ANALYTICS_MAX_LIMIT must be greater than or equal to ANALYTICS_DEFAULT_LIMIT")
        decision_weight = (
            self.decision_service_impact_weight
            + self.decision_urgency_weight
            + self.decision_risk_weight
            + self.decision_feasibility_weight
            + self.decision_policy_alignment_weight
        )
        if abs(decision_weight - 1.0) > 0.001:
            raise ValueError("Decision option weights must add up to 1")
        confidence_weight = (
            self.confidence_retrieval_coverage_weight
            + self.confidence_source_quality_weight
            + self.confidence_data_completeness_weight
            + self.confidence_source_agreement_weight
            + self.confidence_recency_weight
            + self.confidence_model_reliability_weight
        )
        if abs(confidence_weight - 1.0) > 0.001:
            raise ValueError("Decision confidence weights must add up to 1")
        if self.data_science_provider not in {"disabled", "mock", "remote"}:
            raise ValueError("DATA_SCIENCE_PROVIDER must be disabled, mock, or remote")
        if self.data_science_provider == "mock" and not self.allow_mock_data_science:
            raise ValueError("ALLOW_MOCK_DATA_SCIENCE must be true to use the mock provider")
        if self.data_science_provider == "remote" and (not self.ml_service_base_url.startswith(("http://", "https://")) or not self.ml_service_token):
            raise ValueError("Remote Data Science requires ML_SERVICE_BASE_URL and ML_SERVICE_TOKEN")
        if self.auth_provider != "oidc":
            raise ValueError("AUTH_PROVIDER must be oidc")
        algorithms = {item.strip() for item in self.jwt_allowed_algorithms.split(",") if item.strip()}
        if not algorithms or algorithms - {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}:
            raise ValueError("JWT_ALLOWED_ALGORITHMS contains an unsupported algorithm")
        if self.object_storage_backend not in {"local", "s3"}:
            raise ValueError("OBJECT_STORAGE_BACKEND must be local or s3")
        if not self.database_url or not self.database_sync_url:
            raise ValueError("DATABASE_URL and DATABASE_SYNC_URL are required")
        if self.app_environment.casefold() == "production":
            if not self.decision_require_human_approval or self.allow_mock_data_science:
                raise ValueError("Production decisions require human approval and cannot use mock Data Science evidence")
            if not self.auth_enabled:
                raise ValueError("AUTH_ENABLED must be true in production")
            if self.allow_development_auth:
                raise ValueError("Development authentication cannot be enabled in production")
            if not self.oidc_issuer_url.startswith("https://") or not self.oidc_jwks_url.startswith("https://"):
                raise ValueError("Production OIDC issuer and JWKS URLs must use HTTPS")
            origins = {item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()}
            if not origins or any("localhost" in item or "127.0.0.1" in item or not item.startswith("https://") for item in origins):
                raise ValueError("Production CORS origins must be explicit HTTPS origins without localhost")
            if self.enable_retrieval_debug_api or self.analytics_enable_debug_api or self.enable_decision_debug_api:
                raise ValueError("Debug APIs must be disabled in production")
            if not self.rate_limit_enabled or not self.redis_required:
                raise ValueError("Production requires distributed Redis rate limiting")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings object."""
    return Settings()
