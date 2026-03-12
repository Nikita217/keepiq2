from __future__ import annotations

from utils.text import compact_text

from content_extractors.base import ContentExtractor
from domain.models import AnalysisContext, ExtractedContent


class TextExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        chunks = [
            context.payload.raw_text,
            context.payload.caption,
            context.payload.original_caption,
        ]
        text = compact_text("\n".join(chunk for chunk in chunks if chunk))
        if text:
            content.raw_text = text
            content.source_signals.append("text")
        return content

