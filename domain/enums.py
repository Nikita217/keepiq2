from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class SourceType(StrEnum):
    PLAIN_TEXT = "plain_text"
    VOICE_MESSAGE = "voice_message"
    PHOTO = "photo"
    SCREENSHOT = "screenshot"
    FORWARDED_MESSAGE = "forwarded_message"
    LINK = "link"
    DOCUMENT = "document"
    TICKET = "ticket"
    BOOKING_CONFIRMATION = "booking_confirmation"
    RECEIPT = "receipt"
    IMAGE_WITH_TEXT = "image_with_text"
    MIXED_MESSAGE = "mixed_message"
    UNKNOWN = "unknown"


class IntentType(StrEnum):
    REMINDER = "reminder"
    LIST = "list"
    EVENT = "event"
    NOTE = "note"
    INBOX_REVIEW = "inbox_review"
    TASK = "task"
    REPLY_LATER = "reply_later"
    SAVE_ONLY = "save_only"


class FinalType(StrEnum):
    REMINDER = "reminder"
    LIST = "list"
    EVENT = "event"
    NOTE = "note"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionKind(StrEnum):
    CREATE = "create"
    KEEP_IN_INBOX = "keep_in_inbox"


class SuggestionActionType(StrEnum):
    CREATE_REMINDER = "create_reminder"
    CREATE_LIST = "create_list"
    CREATE_EVENT = "create_event"
    CREATE_NOTE = "create_note"
    KEEP_IN_INBOX = "keep_in_inbox"
