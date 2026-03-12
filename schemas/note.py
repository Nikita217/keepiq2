from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class NoteRead(BaseModel):
    id: UUID
    title: str
    body: str | None = None
    kind: str
    source_incoming_item_id: UUID | None = None


class SavedItemRead(BaseModel):
    id: UUID
    title: str
    summary: str | None = None
    source_url: str | None = None
    source_incoming_item_id: UUID | None = None
