from __future__ import annotations

from domain.analysis_models import AnalysisContext, ExtractedContent
from domain.enums import SourceType
from extractors.base import ContentExtractor


class ForwardedMessageExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        if context.payload.forwarded or context.payload.source_type == SourceType.FORWARDED_MESSAGE:
            content.source_signals.append("forwarded")
            forwarded_text = context.payload.metadata.get("forwarded_text") or context.payload.forwarded_text
            if forwarded_text:
                content.forwarded_text = str(forwarded_text)
        return content
