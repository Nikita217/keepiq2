from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from schemas.ai import AnalysisPayload


class AIProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def analyze_text(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        raise NotImplementedError

    @abstractmethod
    async def analyze_image(self, file_path: Path, *, extracted_text: str | None = None) -> AnalysisPayload:
        raise NotImplementedError

    @abstractmethod
    async def transcribe_audio(self, file_path: Path) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        raise NotImplementedError
