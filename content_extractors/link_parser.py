from __future__ import annotations

from urllib.parse import urlparse

from content_extractors.base import ContentExtractor
from domain.models import AnalysisContext, ExtractedContent


class LinkParserExtractor(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        url = context.payload.source_url or context.payload.metadata.get("source_url")
        if not url and content.raw_text:
            for token in content.raw_text.split():
                if token.startswith("http://") or token.startswith("https://"):
                    url = token
                    break
        if not url:
            return content
        parsed = urlparse(url)
        content.metadata["url"] = url
        content.metadata["url_host"] = parsed.netloc
        content.source_signals.append("link")
        return content

