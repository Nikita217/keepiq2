from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common import AttachmentRead, AuditEventRead, ParsedEntityRead


class SuggestedActionRead(BaseModel):
    label: str
    kind: str = "resolve"
    target_type: str | None = None
    due_at: datetime | None = None
    remind_at: datetime | None = None
    event_at: datetime | None = None
    title: str | None = None
    response_text: str | None = None


class IncomingItemRead(BaseModel):
    id: UUID
    incoming_type: str
    parse_status: str
    summary: str | None = None
    proposed_type: str | None = None
    confidence: float | None = None
    needs_confirmation: bool
    raw_text: str | None = None
    transcript_text: str | None = None
    ocr_text: str | None = None
    source_url: str | None = None
    assistant_response: str | None = None
    clarification_question: str | None = None
    resolved_object_type: str | None = None
    suggested_actions: list[SuggestedActionRead] = Field(default_factory=list)
    created_at: datetime
    attachments: list[AttachmentRead] = Field(default_factory=list)
    entities: list[ParsedEntityRead] = Field(default_factory=list)
    logs: list[AuditEventRead] = Field(default_factory=list)


class InboxActionRequest(BaseModel):
    target_type: str | None = None
    title: str | None = None
    force_confirmation: bool = False
    suggested_action_id: int | None = None


class IncomingUpdateRequest(BaseModel):
    proposed_type: str | None = None
    summary: str | None = None
    needs_confirmation: bool | None = None
    parse_status: str | None = None
