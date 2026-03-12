from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import IncomingType, ObjectType, ParseStatus


class IncomingItem(Base, TimestampMixin):
    __tablename__ = "incoming_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    telegram_message_id: Mapped[int | None] = mapped_column(index=True)
    telegram_update_id: Mapped[int | None] = mapped_column(index=True)
    original_chat_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    original_message_id: Mapped[int | None] = mapped_column(index=True)
    incoming_type: Mapped[str] = mapped_column(String(32), default=IncomingType.UNKNOWN.value, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    transcript_text: Mapped[str | None] = mapped_column(Text)
    ocr_text: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    original_caption: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    parsed_entities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    analysis_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    linked_objects_json: Mapped[list] = mapped_column(JSON, default=list)
    parse_status: Mapped[str] = mapped_column(String(32), default=ParseStatus.NEW.value, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    proposed_type: Mapped[str | None] = mapped_column(String(32))
    summary: Mapped[str | None] = mapped_column(Text)
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="incoming_items")
    attachments = relationship("Attachment", back_populates="incoming_item", cascade="all, delete-orphan")
    entities = relationship("ParsedEntity", back_populates="incoming_item", cascade="all, delete-orphan")
    analysis_results = relationship(
        "AIAnalysisResult", back_populates="incoming_item", cascade="all, delete-orphan"
    )
    object_links = relationship("ObjectLink", back_populates="incoming_item", cascade="all, delete-orphan")
    processing_logs = relationship(
        "ProcessingLog", back_populates="incoming_item", cascade="all, delete-orphan"
    )


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    incoming_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="CASCADE"), index=True
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    telegram_unique_file_id: Mapped[str | None] = mapped_column(String(255))
    file_name: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(32), index=True)
    local_path: Mapped[str | None] = mapped_column(Text)
    file_size: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    incoming_item = relationship("IncomingItem", back_populates="attachments")


class ParsedEntity(Base, TimestampMixin):
    __tablename__ = "parsed_entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    incoming_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[str] = mapped_column(Text)
    normalized_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(32))

    incoming_item = relationship("IncomingItem", back_populates="entities")


class AIAnalysisResult(Base, TimestampMixin):
    __tablename__ = "ai_analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    incoming_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    summary: Mapped[str | None] = mapped_column(Text)
    proposed_type: Mapped[str | None] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)

    incoming_item = relationship("IncomingItem", back_populates="analysis_results")


class ObjectLink(Base, TimestampMixin):
    __tablename__ = "object_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    incoming_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="CASCADE"), index=True
    )
    object_type: Mapped[str] = mapped_column(String(32), default=ObjectType.NOTE.value, index=True)
    object_id: Mapped[str] = mapped_column(String(64), index=True)

    incoming_item = relationship("IncomingItem", back_populates="object_links")

