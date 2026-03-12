from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ListItemRead(BaseModel):
    id: UUID
    text: str
    is_done: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ListRead(BaseModel):
    id: UUID
    title: str
    kind: str
    description: str | None = None
    source_incoming_item_id: UUID | None = None
    items: list[ListItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ListItemWrite(BaseModel):
    id: UUID | None = None
    text: str
    is_done: bool = False
    sort_order: int = 0


class ListUpdateRequest(BaseModel):
    title: str | None = None
    kind: str | None = None
    description: str | None = None
    items: list[ListItemWrite] | None = None
