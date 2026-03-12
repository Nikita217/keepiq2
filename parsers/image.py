from __future__ import annotations

from pathlib import Path

from ai.base import AIProvider
from schemas.ai import AnalysisPayload


class ImageParser:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def analyze(self, file_path: Path, *, extracted_text: str | None = None) -> AnalysisPayload:
        return await self.provider.analyze_image(file_path, extracted_text=extracted_text)
