from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    locale: Mapped[str] = mapped_column(String(16), default="ru")
    auto_create_high_confidence: Mapped[bool] = mapped_column(Boolean, default=True)
    default_reminder_lead_hours: Mapped[int] = mapped_column(default=3)
    enable_ai_reply_drafts: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="settings")


class DailyDigestSettings(Base, TimestampMixin):
    __tablename__ = "daily_digest_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    morning_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    morning_time: Mapped[str] = mapped_column(String(5), default="09:00")
    evening_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    evening_time: Mapped[str] = mapped_column(String(5), default="20:30")
    include_overdue: Mapped[bool] = mapped_column(Boolean, default=True)
    include_inbox: Mapped[bool] = mapped_column(Boolean, default=True)
    include_events: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="digest_settings")
