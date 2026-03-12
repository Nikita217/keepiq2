from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    entity_type: str
    value: str
    normalized_value: str | None = None
    confidence: float | None = None


class CandidateObject(BaseModel):
    object_type: str
    title: str
    description: str | None = None
    due_at: datetime | None = None
    remind_at: datetime | None = None
    event_at: datetime | None = None
    category_hint: str | None = None
    items: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class AnalysisPayload(BaseModel):
    provider: str
    model: str | None = None
    summary: str
    proposed_type: str
    confidence: float
    needs_confirmation: bool
    extracted_entities: list[ExtractedEntity] = Field(default_factory=list)
    candidates: list[CandidateObject] = Field(default_factory=list)
    draft_replies: dict[str, str] = Field(default_factory=dict)
    assistant_response: str | None = None
    clarification_question: str | None = None
    raw: dict = Field(default_factory=dict)
