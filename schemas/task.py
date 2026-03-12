from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TaskRead(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    status: str
    due_at: datetime | None = None
    scheduled_for: datetime | None = None
    priority: str
    source_incoming_item_id: UUID | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_at: datetime | None = None
    scheduled_for: datetime | None = None
