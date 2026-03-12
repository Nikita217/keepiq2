from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    q: str = ""
    object_types: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    category: str | None = None
    from_date: str | None = None
    to_date: str | None = None


class SearchResultItem(BaseModel):
    object_type: str
    object_id: UUID | str
    title: str
    snippet: str | None = None
    status: str | None = None
    source_incoming_item_id: UUID | None = None


class SearchResponse(BaseModel):
    items: list[SearchResultItem]
