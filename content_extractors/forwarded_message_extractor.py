from __future__ import annotations

from content_extractors.base import ContentExtractor
from domain.enums import SourceType
from domain.models import AnalysisContext, ExtractedContent


class ForwardedMessageExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        if context.payload.forwarded or context.payload.source_type == SourceType.FORWARDED_MESSAGE:
            content.source_signals.append("forwarded")
            forward_origin = context.payload.metadata.get("forward_origin")
            if forward_origin:
                content.metadata["forward_origin"] = forward_origin
        return content

