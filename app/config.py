from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(..., alias="DATABASE_URL")
    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field("deepseek/deepseek-chat", alias="OPENROUTER_MODEL")
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    db_timeout: int = Field(default=10, alias="DB_TIMEOUT")
    rate_limit_seconds: int = Field(default=3, alias="RATE_LIMIT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
