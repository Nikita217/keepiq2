from __future__ import annotations

from datetime import date as Date, datetime as DateTime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums import ConfidenceLevel, FinalType, SourceType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class NormalizedAttachment(StrictModel):
    telegram_file_id: str | None = None
    telegram_unique_file_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    media_type: str | None = None
    local_path: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None


class NormalizedIncomingPayload(StrictModel):
    incoming_id: str | None = None
    user_id: int
    source_type: SourceType
    raw_text: str | None = None
    caption: str | None = None
    forwarded_text: str | None = None
    source_url: str | None = None
    media_type: str | None = None
    forwarded: bool = False
    original_message_id: int | None = None
    original_chat_id: int | None = None
    original_caption: str | None = None
    attachments: list[NormalizedAttachment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedContent(StrictModel):
    raw_text: str | None = None
    extracted_text: str | None = None
    transcript: str | None = None
    ocr_text: str | None = None
    caption: str | None = None
    forwarded_text: str | None = None
    detected_language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_signals: list[str] = Field(default_factory=list)
    extraction_errors: list[str] = Field(default_factory=list)


class AnalysisContext(StrictModel):
    now: DateTime
    timezone: str
    payload: NormalizedIncomingPayload
    extracted: ExtractedContent


class RelativeOffset(StrictModel):
    value: int
    unit: Literal["days", "weeks", "months", "hours"]
    direction: Literal["before", "after"]


class ExtractedEntities(StrictModel):
    dates: list[str] = Field(default_factory=list)
    times: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    places: list[str] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)


class ReasoningFlags(StrictModel):
    contains_background_motivation: bool = False
    contains_actionable_request: bool = False
    contains_event_context: bool = False
    contains_multiple_independent_actions: bool = False
    contains_list_pattern: bool = False
    ambiguous_datetime: bool = False


class AIAnalysisItem(StrictModel):
    type: FinalType
    title: str
    description: str | None = None
    list_items: list[str] = Field(default_factory=list)
    datetime: DateTime | None = None
    date_only: Date | None = None
    event_date: DateTime | None = None
    relative_offset: RelativeOffset | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AIAnalysisResult(StrictModel):
    source_type: SourceType
    normalized_text: str
    summary: str
    primary_type: FinalType
    secondary_candidate_type: FinalType | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_user_confirmation: bool
    items: list[AIAnalysisItem] = Field(default_factory=list)
    extracted_entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    reasoning_flags: ReasoningFlags = Field(default_factory=ReasoningFlags)


class ResolvedAnalysisItem(StrictModel):
    type: FinalType
    title: str
    description: str | None = None
    list_items: list[str] = Field(default_factory=list)
    resolved_datetime: DateTime | None = None
    resolved_date: Date | None = None
    event_datetime: DateTime | None = None
    relative_offset: RelativeOffset | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_item_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolvedAnalysisResult(StrictModel):
    source_type: SourceType
    normalized_text: str
    summary: str
    primary_type: FinalType
    secondary_candidate_type: FinalType | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    needs_user_confirmation: bool = True
    items: list[ResolvedAnalysisItem] = Field(default_factory=list)
    extracted_entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    reasoning_flags: ReasoningFlags = Field(default_factory=ReasoningFlags)

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))