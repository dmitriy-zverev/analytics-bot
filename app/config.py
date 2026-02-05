"""Application configuration management.

Uses Pydantic Settings for environment-based configuration with
type validation and sensible defaults.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables are loaded from .env file and validated
    against these type definitions. All settings have sensible defaults
    where appropriate.

    Required environment variables:
        - DATABASE_URL: PostgreSQL connection string
        - TELEGRAM_TOKEN: Bot token from @BotFather
        - OPENROUTER_API_KEY: API key for OpenRouter

    Optional environment variables:
        - OPENROUTER_MODEL: LLM model to use (default: deepseek/deepseek-chat)
        - LLM_TIMEOUT: Seconds to wait for LLM response (default: 30)
        - DB_TIMEOUT: Seconds to wait for DB query (default: 10)
        - RATE_LIMIT_SECONDS: Min seconds between user requests (default: 3)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra env vars without validation errors
    )

    # Database configuration
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="PostgreSQL async connection URL",
    )

    # Telegram Bot configuration
    telegram_token: str = Field(
        ...,
        alias="TELEGRAM_TOKEN",
        description="Token from @BotFather",
    )

    # LLM Provider configuration
    openrouter_api_key: str = Field(
        ...,
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API authentication key",
    )
    openrouter_model: str = Field(
        "deepseek/deepseek-chat",
        alias="OPENROUTER_MODEL",
        description="Model identifier for SQL generation",
    )

    # Timeout configuration (in seconds)
    llm_timeout: int = Field(
        30,
        alias="LLM_TIMEOUT",
        description="Maximum wait time for LLM API response",
        ge=1,  # Must be at least 1 second
        le=300,  # Max 5 minutes
    )
    db_timeout: int = Field(
        10,
        alias="DB_TIMEOUT",
        description="Maximum wait time for database query",
        ge=1,
        le=60,
    )

    # Rate limiting configuration
    rate_limit_seconds: int = Field(
        3,
        alias="RATE_LIMIT_SECONDS",
        description="Minimum seconds between requests from same user",
        ge=1,
        le=300,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached Settings instance.

    Uses LRU cache to avoid reloading .env file on every call.
    Settings are loaded once at startup and reused.

    Returns:
        Settings: Application configuration singleton

    Example:
        settings = get_settings()
        db_url = settings.database_url
    """
    return Settings()  # type: ignore[call-arg]
