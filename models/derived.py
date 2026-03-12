from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin
from models.enums import EventStatus, ImportanceLevel, NoteStatus, ReminderStatus, TaskStatus


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.INBOX.value, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    priority: Mapped[str] = mapped_column(String(16), default=ImportanceLevel.MEDIUM.value)
    confidence: Mapped[float | None] = mapped_column(Float)
    category_hint: Mapped[str | None] = mapped_column(String(64))
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    remind_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    remind_on: Mapped[date | None] = mapped_column(Date, index=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default=ReminderStatus.ACTIVE.value, index=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    place_name: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    booking_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default=EventStatus.UPCOMING.value, index=True)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=NoteStatus.ACTIVE.value)
    kind: Mapped[str] = mapped_column(String(32), default="note", index=True)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ListEntity(Base, TimestampMixin):
    __tablename__ = "lists"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(32), default="general", index=True)
    description: Mapped[str | None] = mapped_column(Text)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ListItem(Base, TimestampMixin):
    __tablename__ = "list_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lists.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(255))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(default=0)


class ReplyLaterItem(Base, TimestampMixin):
    __tablename__ = "reply_later_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    conversation_summary: Mapped[str | None] = mapped_column(Text)
    suggested_replies_json: Mapped[dict] = mapped_column(JSON, default=dict)
    reply_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)


class SavedItem(Base, TimestampMixin):
    __tablename__ = "saved_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)
