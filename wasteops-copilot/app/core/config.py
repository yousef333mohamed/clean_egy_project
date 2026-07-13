"""Environment-backed application configuration."""

from functools import lru_cache
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables or .env."""

    app_name: str = "WasteOps Decision Intelligence Copilot"
    app_environment: str = "development"
    log_level: str = "INFO"
    database_url: str
    database_sync_url: str
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
    confidence_source_quality_weight: float = Field(default=0.25, ge=0, le=1)
    confidence_data_completeness_weight: float = Field(default=0.20, ge=0, le=1)
    confidence_source_agreement_weight: float = Field(default=0.15, ge=0, le=1)
    confidence_recency_weight: float = Field(default=0.15, ge=0, le=1)
    data_science_provider: str = "disabled"
    allow_mock_data_science: bool = False

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
        )
        if abs(confidence_weight - 1.0) > 0.001:
            raise ValueError("Decision confidence weights must add up to 1")
        if self.data_science_provider not in {"disabled", "mock"}:
            raise ValueError("DATA_SCIENCE_PROVIDER must be disabled or mock in this step")
        if self.data_science_provider == "mock" and not self.allow_mock_data_science:
            raise ValueError("ALLOW_MOCK_DATA_SCIENCE must be true to use the mock provider")
        if self.app_environment.casefold() == "production" and (not self.decision_require_human_approval or self.allow_mock_data_science):
            raise ValueError("Production decisions require human approval and cannot use mock Data Science evidence")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings object."""
    return Settings()
