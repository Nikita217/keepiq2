from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NoteRead(BaseModel):
    id: UUID
    title: str
    body: str | None = None
    status: str
    kind: str
    source_incoming_item_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class SavedItemRead(BaseModel):
    id: UUID
    title: str
    summary: str | None = None
    source_url: str | None = None
    source_incoming_item_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ReplyLaterRead(BaseModel):
    id: UUID
    title: str
    conversation_summary: str | None = None
    reply_due_at: datetime | None = None
    status: str
    suggested_replies: dict
    source_incoming_item_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class NoteUpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    kind: str | None = None
    status: str | None = None


class ReplyLaterUpdateRequest(BaseModel):
    title: str | None = None
    conversation_summary: str | None = None
    reply_due_at: datetime | None = None
    status: str | None = None


class SavedItemUpdateRequest(BaseModel):
    title: str | None = None
    summary: str | None = None
    source_url: str | None = None
