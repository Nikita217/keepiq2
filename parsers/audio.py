from __future__ import annotations

from pathlib import Path

from ai.base import AIProvider


class AudioParser:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def transcribe(self, file_path: Path) -> str:
        return await self.provider.transcribe_audio(file_path)
