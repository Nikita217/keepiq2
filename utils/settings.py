from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

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
    openai_reasoning_effort: str = Field(default="medium", alias="OPENAI_REASONING_EFFORT")
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
    ai_timeout_seconds: float = Field(default=20.0, alias="AI_TIMEOUT_SECONDS")
    ai_max_retries: int = Field(default=2, alias="AI_MAX_RETRIES")
    ai_high_confidence_threshold: float = Field(default=0.85, alias="AI_HIGH_CONFIDENCE_THRESHOLD")
    ai_medium_confidence_threshold: float = Field(default=0.60, alias="AI_MEDIUM_CONFIDENCE_THRESHOLD")
    ai_default_reminder_times: list[str] = Field(
        default_factory=lambda: ["10:00", "12:00", "18:00"],
        alias="AI_DEFAULT_REMINDER_TIMES",
    )
    ai_default_event_times: list[str] = Field(
        default_factory=lambda: ["10:00", "18:00"],
        alias="AI_DEFAULT_EVENT_TIMES",
    )
    ai_task_suggestion_hours: list[int] = Field(default_factory=lambda: [12, 15, 18], alias="AI_TASK_SUGGESTION_HOURS")
    ai_date_only_event_suggestion_hours: list[int] = Field(
        default_factory=lambda: [9, 14, 19], alias="AI_DATE_ONLY_EVENT_SUGGESTION_HOURS"
    )
    ai_reply_later_presets: list[str] = Field(
        default_factory=lambda: ["today_evening", "tomorrow_morning", "next_monday_morning"],
        alias="AI_REPLY_LATER_PRESETS",
    )

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql") or self.database_url.startswith("postgresql+")

    @property
    def cors_allowed_origins(self) -> list[str]:
        origins: list[str] = []
        for candidate in (self.mini_app_dev_url, self.mini_app_public_url):
            normalized = self._normalize_origin(candidate)
            if normalized and normalized not in origins:
                origins.append(normalized)
        return origins

    @staticmethod
    def _normalize_origin(candidate: str) -> str:
        raw = candidate.strip().rstrip("/")
        if not raw:
            return ""
        parsed = urlparse(raw)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return raw


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.local_storage_root.mkdir(parents=True, exist_ok=True)
    return settings
