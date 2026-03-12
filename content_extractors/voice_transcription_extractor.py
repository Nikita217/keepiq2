from __future__ import annotations

from pathlib import Path

from ai.base import AIProvider
from content_extractors.base import ContentExtractor
from domain.enums import SourceType
from domain.models import AnalysisContext, ExtractedContent


class VoiceTranscriptionExtractor(ContentExtractor):
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        if context.payload.source_type != SourceType.VOICE_MESSAGE:
            return content
        attachment = next((item for item in context.payload.attachments if item.local_path), None)
        if attachment is None or not attachment.local_path:
            content.extraction_errors.append("voice_attachment_missing")
            return content
        try:
            content.transcript = await self.provider.transcribe_audio(Path(attachment.local_path))
            if content.transcript:
                content.source_signals.append("transcript")
        except Exception as exc:
            content.extraction_errors.append(f"voice_transcription_failed:{exc}")
        return content

