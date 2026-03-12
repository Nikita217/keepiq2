from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ReminderRead(BaseModel):
    id: UUID
    title: str
    status: str
    remind_at: datetime | None = None
    remind_on: date | None = None
    snoozed_until: datetime | None = None
    source_incoming_item_id: UUID | None = None
