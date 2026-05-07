from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    line_channel_secret: str = Field(..., validation_alias="LINE_CHANNEL_SECRET")
    line_channel_access_token: str = Field(..., validation_alias="LINE_CHANNEL_ACCESS_TOKEN")
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(1000, validation_alias="OPENAI_MAX_TOKENS")
    max_history_messages: int = Field(10, validation_alias="MAX_HISTORY_MESSAGES")
    app_env: str = Field("production", validation_alias="APP_ENV")
    redis_url: Optional[str] = Field(None, validation_alias="REDIS_URL")

    model_config = {"env_file": ".env", "case_sensitive": False, "populate_by_name": True}


@lru_cache
def get_settings() -> Settings:
    return Settings()
