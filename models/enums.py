from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class IncomingType(StrEnum):
    PLAIN_TEXT = "plain_text"
    TEXT = "plain_text"
    VOICE_MESSAGE = "voice_message"
    VOICE = "voice_message"
    AUDIO = "voice_message"
    PHOTO = "photo"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    FORWARDED_MESSAGE = "forwarded_message"
    FORWARDED = "forwarded_message"
    LINK = "link"
    TICKET = "ticket"
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING = "booking_confirmation"
    RECEIPT = "receipt"
    IMAGE_WITH_TEXT = "image_with_text"
    IMAGE = "image_with_text"
    MIXED_MESSAGE = "mixed_message"
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
    SAVE_ONLY = "save_only"
    SAVED = "save_only"
    INBOX_REVIEW = "inbox_review"


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

