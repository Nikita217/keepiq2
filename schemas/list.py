from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ListItemRead(BaseModel):
    id: UUID
    text: str
    is_done: bool
    sort_order: int


class ListRead(BaseModel):
    id: UUID
    title: str
    kind: str
    description: str | None = None
    source_incoming_item_id: UUID | None = None
    items: list[ListItemRead] = Field(default_factory=list)
