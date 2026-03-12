from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="KeepIQ", alias="APP_NAME")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_vision_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_VISION_MODEL")
    openai_audio_model: str = Field(default="gpt-4o-mini-transcribe", alias="OPENAI_AUDIO_MODEL")
    database_url: str = Field(default="sqlite+aiosqlite:///./keepiq.db", alias="DATABASE_URL")
    local_storage_root: Path = Field(default=Path("./uploads"), alias="LOCAL_STORAGE_ROOT")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    mini_app_dev_url: str = Field(default="http://localhost:5173", alias="MINI_APP_DEV_URL")
    mini_app_public_url: str = Field(default="", alias="MINI_APP_PUBLIC_URL")
    webhook_base_url: str = Field(default="", alias="WEBHOOK_BASE_URL")
    use_webhook: bool = Field(default=False, alias="USE_WEBHOOK")
    ocr_enabled: bool = Field(default=True, alias="OCR_ENABLED")
    voice_transcription_enabled: bool = Field(default=True, alias="VOICE_TRANSCRIPTION_ENABLED")
    init_data_max_age_seconds: int = Field(default=3600, alias="INIT_DATA_MAX_AGE_SECONDS")
    default_reminder_lead_hours: int = Field(default=3, alias="DEFAULT_REMINDER_LEAD_HOURS")
    morning_digest_enabled: bool = Field(default=True, alias="MORNING_DIGEST_ENABLED")
    morning_digest_time: str = Field(default="09:00", alias="MORNING_DIGEST_TIME")
    evening_digest_enabled: bool = Field(default=True, alias="EVENING_DIGEST_ENABLED")
    evening_digest_time: str = Field(default="20:30", alias="EVENING_DIGEST_TIME")

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql") or self.database_url.startswith("postgresql+")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.local_storage_root.mkdir(parents=True, exist_ok=True)
    return settings
