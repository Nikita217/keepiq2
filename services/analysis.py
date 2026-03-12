from __future__ import annotations

from pathlib import Path

from ai.base import AIProvider
from models.enums import IncomingType
from parsers.audio import AudioParser
from parsers.image import ImageParser
from parsers.text import HeuristicTextParser
from schemas.ai import AnalysisPayload


class AnalysisService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider
        self.audio_parser = AudioParser(provider)
        self.image_parser = ImageParser(provider)
        self.text_parser = HeuristicTextParser()

    async def analyze_text(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        if not text.strip():
            return self.text_parser.analyze("Пустой ввод", hint=hint)
        try:
            return await self.provider.analyze_text(text, hint=hint)
        except Exception:
            return self.text_parser.analyze(text, hint=hint)

    async def transcribe_audio(self, file_path: Path) -> str:
        try:
            return await self.audio_parser.transcribe(file_path)
        except Exception:
            return f"Голосовое сохранено: {file_path.name}"

    async def analyze_image(self, file_path: Path, *, extracted_text: str | None = None) -> AnalysisPayload:
        try:
            return await self.image_parser.analyze(file_path, extracted_text=extracted_text)
        except Exception:
            return self.text_parser.analyze(extracted_text or file_path.name, hint="image")

    async def analyze_incoming(
        self,
        *,
        incoming_type: str,
        raw_text: str | None = None,
        transcript_text: str | None = None,
        ocr_text: str | None = None,
        file_path: Path | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        metadata: dict | None = None,
        forwarded: bool = False,
    ) -> AnalysisPayload:
        hint = None
        if incoming_type in {IncomingType.TICKET.value, IncomingType.BOOKING.value}:
            hint = "ticket"
        elif incoming_type == IncomingType.FORWARDED.value or forwarded:
            hint = "forwarded"
        elif incoming_type in {IncomingType.VOICE.value, IncomingType.AUDIO.value}:
            hint = "voice"
        elif incoming_type in {IncomingType.PHOTO.value, IncomingType.SCREENSHOT.value, IncomingType.IMAGE.value}:
            hint = "image"

        context_text = self._compose_context_text(
            incoming_type=incoming_type,
            raw_text=raw_text,
            transcript_text=transcript_text,
            ocr_text=ocr_text,
            file_name=file_name,
            mime_type=mime_type,
            metadata=metadata,
            forwarded=forwarded,
        )

        if incoming_type in {IncomingType.PHOTO.value, IncomingType.SCREENSHOT.value, IncomingType.IMAGE.value} and file_path:
            return await self.analyze_image(file_path, extracted_text=context_text)
        return await self.analyze_text(context_text, hint=hint)

    def _compose_context_text(
        self,
        *,
        incoming_type: str,
        raw_text: str | None,
        transcript_text: str | None,
        ocr_text: str | None,
        file_name: str | None,
        mime_type: str | None,
        metadata: dict | None,
        forwarded: bool,
    ) -> str:
        parts: list[str] = [f"type: {incoming_type}"]
        if forwarded:
            parts.append("forwarded: yes")
        if file_name:
            parts.append(f"filename: {file_name}")
        if mime_type:
            parts.append(f"mime: {mime_type}")
        if metadata:
            caption = metadata.get("caption")
            if caption:
                parts.append(f"caption: {caption}")
            media_title = metadata.get("title")
            if media_title:
                parts.append(f"media_title: {media_title}")
        if raw_text:
            parts.append(f"user_text: {raw_text}")
        if transcript_text:
            parts.append(f"transcript: {transcript_text}")
        if ocr_text:
            parts.append(f"ocr_text: {ocr_text}")
        return "\n".join(parts)
