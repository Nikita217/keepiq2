from __future__ import annotations

from domain.analysis_models import AnalysisContext, ExtractedContent
from domain.enums import SourceType
from extractors.base import ContentExtractor

TICKET_HINTS = ("ticket", "билет", "concert", "flight", "train", "booking", "бронь", "reservation")
RECEIPT_HINTS = ("receipt", "чек", "invoice", "квитанц")


class TicketBookingParser(ContentExtractor):
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        attachment_names = [item.file_name.lower() for item in context.payload.attachments if item.file_name]
        semantic_text = " ".join(fragment for fragment in [content.raw_text, content.ocr_text, context.payload.caption] if fragment).lower()
        haystack = " ".join([semantic_text, *attachment_names])
        if any(hint in haystack for hint in TICKET_HINTS) or context.payload.source_type in {SourceType.TICKET, SourceType.BOOKING_CONFIRMATION}:
            content.metadata["document_hint"] = "ticket_or_booking"
            content.source_signals.append("ticket_or_booking")
        elif context.payload.source_type == SourceType.RECEIPT or any(hint in haystack for hint in RECEIPT_HINTS):
            content.metadata["document_hint"] = "receipt"
            content.source_signals.append("receipt")
        return content
