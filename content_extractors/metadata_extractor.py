from __future__ import annotations

from content_extractors.base import ContentExtractor
from domain.models import AnalysisContext, ExtractedContent


class MetadataExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        media_hints: list[str] = []
        for attachment in context.payload.attachments:
            if attachment.file_name:
                media_hints.append(attachment.file_name)
            if attachment.mime_type:
                media_hints.append(attachment.mime_type)
        content.metadata.update(context.payload.metadata)
        if context.payload.media_type:
            content.metadata["media_type"] = context.payload.media_type
        if media_hints:
            content.metadata["attachment_hints"] = media_hints
        return content

