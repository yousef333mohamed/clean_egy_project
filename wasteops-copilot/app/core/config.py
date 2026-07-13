"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables or .env."""

    app_name: str = "WasteOps Decision Intelligence Copilot"
    app_environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://wasteops:wasteops@localhost:5432/wasteops"
    llm_api_key: str = Field(default="", repr=False)
    llm_base_url: str = "https://api.openai.com/v1"
    chat_model_name: str = "gpt-4.1-mini"
    embedding_model_name: str = "text-embedding-3-small"
    vector_dimensions: int = Field(default=1536, ge=1)
    retrieval_top_k: int = Field(default=8, ge=1, le=100)
    sql_query_timeout_ms: int = Field(default=5000, ge=100)
    sql_row_limit: int = Field(default=200, ge=1, le=5000)
    data_dir: Path = Path("data")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings object."""
    return Settings()
