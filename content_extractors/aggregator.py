from __future__ import annotations

from content_extractors.base import ContentExtractor
from domain.models import AnalysisContext, ExtractedContent
from utils.text import compact_text


class ContentExtractionService:
    def __init__(self, extractors: list[ContentExtractor]) -> None:
        self.extractors = extractors

    async def extract(self, context: AnalysisContext) -> ExtractedContent:
        content = ExtractedContent(raw_text=context.payload.raw_text)
        for extractor in self.extractors:
            content = await extractor.extract(context, content)
        content.extracted_text = self._merge_text(content)
        return content

    def _merge_text(self, content: ExtractedContent) -> str | None:
        ordered_parts = [content.raw_text, content.transcript, content.ocr_text]
        merged = compact_text("\n".join(part for part in ordered_parts if part))
        return merged or None

