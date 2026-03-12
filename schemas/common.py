from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AttachmentRead(ORMModel):
    id: UUID
    content_type: str
    file_name: str | None = None
    local_path: str | None = None
    mime_type: str | None = None


class ParsedEntityRead(ORMModel):
    entity_type: str
    value: str
    normalized_value: str | None = None
    confidence: float | None = None


class SummaryCount(BaseModel):
    name: str
    value: int


class ReminderAction(BaseModel):
    reminder_id: UUID
    action: str
    snooze_minutes: int | None = None


class DateFilter(BaseModel):
    from_date: date | None = None
    to_date: date | None = None


class AuditEventRead(ORMModel):
    stage: str
    level: str
    message: str
    created_at: datetime
