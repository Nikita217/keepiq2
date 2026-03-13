from __future__ import annotations

from domain.analysis_models import AnalysisContext, ExtractedContent
from extractors.base import ContentExtractor
from utils.text import compact_text


class TextExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        chunks = [
            context.payload.raw_text,
            context.payload.caption,
            context.payload.original_caption,
        ]
        raw_text = compact_text("\n".join(chunk for chunk in chunks if chunk))
        if raw_text:
            content.raw_text = raw_text
            content.source_signals.append("text")
        return content
