from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(..., alias="DATABASE_URL")
    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field("deepseek/deepseek-chat", alias="OPENROUTER_MODEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
