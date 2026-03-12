from __future__ import annotations

from pydantic import BaseModel, Field


class DigestResponse(BaseModel):
    title: str
    lines: list[str] = Field(default_factory=list)
