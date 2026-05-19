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
    openai_temperature: float = Field(0.4, validation_alias="OPENAI_TEMPERATURE")
    max_history_messages: int = Field(10, validation_alias="MAX_HISTORY_MESSAGES")
    app_env: str = Field("production", validation_alias="APP_ENV")
    redis_url: Optional[str] = Field(None, validation_alias="REDIS_URL")
    sentry_dsn: Optional[str] = Field(None, validation_alias="SENTRY_DSN")
    daily_message_limit: int = Field(100, validation_alias="DAILY_MESSAGE_LIMIT")
    max_context_tokens: int = Field(3500, validation_alias="MAX_CONTEXT_TOKENS")
    tony_line_user_id: str = Field("", validation_alias="TONY_LINE_USER_ID")
    google_spreadsheet_id: str = Field(
        "184d7kpY7swRCwSJ_eZi8UtrH2K57U1Wzb2Fc9_ShVC8",
        validation_alias="GOOGLE_SPREADSHEET_ID",
    )
    agents_enabled: bool = Field(True, validation_alias="AGENTS_ENABLED")
    drive_folder_id: str = Field("", validation_alias="DRIVE_FOLDER_ID")

    model_config = {"env_file": ".env", "case_sensitive": False, "populate_by_name": True}


@lru_cache
def get_settings() -> Settings:
    return Settings()
