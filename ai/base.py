from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from domain.analysis_models import AIAnalysisResult, AnalysisContext


class AIProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def analyze(self, context: AnalysisContext) -> AIAnalysisResult:
        raise NotImplementedError

    @abstractmethod
    async def transcribe_audio(self, file_path: Path) -> str:
        raise NotImplementedError

    async def extract_image_text(self, file_path: Path) -> str | None:
        return None

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        return {}
