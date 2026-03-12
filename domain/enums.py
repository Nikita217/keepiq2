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
    TASK = "task"
    REMINDER = "reminder"
    EVENT = "event"
    NOTE = "note"
    LIST = "list"
    REPLY_LATER = "reply_later"
    SAVE_ONLY = "save_only"
    INBOX_REVIEW = "inbox_review"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionActionType(StrEnum):
    CREATE_TASK = "create_task"
    CREATE_REMINDER = "create_reminder"
    CREATE_EVENT = "create_event"
    CREATE_NOTE = "create_note"
    CREATE_LIST = "create_list"
    CREATE_REPLY_LATER = "create_reply_later"
    SAVE_ONLY = "save_only"
    SEND_TO_INBOX = "send_to_inbox"
    REVIEW_NOW = "review_now"
    SAVE_ALL = "save_all"
    KEEP_ONLY_TASKS = "keep_only_tasks"

