from __future__ import annotations

from domain.analysis_models import AnalysisContext, ExtractedContent
from extractors.base import ContentExtractor


class MetadataExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        media_hints: list[str] = []
        for attachment in context.payload.attachments:
            if attachment.file_name:
                media_hints.append(attachment.file_name)
            if attachment.mime_type:
                media_hints.append(attachment.mime_type)
        content.metadata.update(context.payload.metadata)
        content.caption = context.payload.caption
        content.forwarded_text = context.payload.forwarded_text
        if context.payload.media_type:
            content.metadata["media_type"] = context.payload.media_type
        if media_hints:
            content.metadata["attachment_hints"] = media_hints
        return content
