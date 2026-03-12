from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class IncomingType(StrEnum):
    TEXT = "text"
    VOICE = "voice"
    AUDIO = "audio"
    PHOTO = "photo"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    FORWARDED = "forwarded"
    LINK = "link"
    TICKET = "ticket"
    BOOKING = "booking"
    RECEIPT = "receipt"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ParseStatus(StrEnum):
    NEW = "new"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ObjectType(StrEnum):
    TASK = "task"
    REMINDER = "reminder"
    EVENT = "event"
    NOTE = "note"
    LIST = "list"
    REPLY_LATER = "reply_later"
    SAVED = "saved"


class TaskStatus(StrEnum):
    INBOX = "inbox"
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    WAITING_REPLY = "waiting_reply"
    DONE = "done"
    ARCHIVED = "archived"
    SOMEDAY = "someday"


class ReminderStatus(StrEnum):
    ACTIVE = "active"
    SNOOZED = "snoozed"
    DONE = "done"
    CANCELLED = "cancelled"


class EventStatus(StrEnum):
    UPCOMING = "upcoming"
    DONE = "done"
    CANCELLED = "cancelled"


class NoteStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ImportanceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DigestKind(StrEnum):
    MORNING = "morning"
    EVENING = "evening"
