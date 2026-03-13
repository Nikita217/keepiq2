from __future__ import annotations

from pathlib import Path

from ai.base import AIProvider
from domain.analysis_models import AnalysisContext, ExtractedContent
from domain.enums import SourceType
from extractors.base import ContentExtractor
from utils.text import compact_text


class OCRExtractor(ContentExtractor):
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        if context.payload.source_type not in {
            SourceType.PHOTO,
            SourceType.SCREENSHOT,
            SourceType.DOCUMENT,
            SourceType.TICKET,
            SourceType.BOOKING_CONFIRMATION,
            SourceType.RECEIPT,
            SourceType.IMAGE_WITH_TEXT,
            SourceType.MIXED_MESSAGE,
        }:
            return content

        attachment = next((item for item in context.payload.attachments if item.local_path), None)
        existing_text = context.payload.metadata.get("ocr_text") or context.payload.metadata.get("extracted_text")
        if existing_text:
            content.ocr_text = compact_text(str(existing_text))
            content.source_signals.append("ocr")
            return content

        if attachment is None or not attachment.local_path:
            return content

        try:
            extracted = await self.provider.extract_image_text(Path(attachment.local_path))
        except Exception as exc:
            content.extraction_errors.append(f"ocr_failed:{exc}")
            return content
        if extracted:
            content.ocr_text = compact_text(extracted)
            content.source_signals.append("ocr")
        return content
