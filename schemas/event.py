from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventRead(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    place_name: str | None = None
    address: str | None = None
    booking_reference: str | None = None
    status: str
    source_incoming_item_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class EventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    place_name: str | None = None
    address: str | None = None
    booking_reference: str | None = None
    status: str | None = None
