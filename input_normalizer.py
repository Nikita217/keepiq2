from __future__ import annotations

from models import Attachment, IncomingItem
from domain.enums import SourceType
from domain.models import NormalizedAttachment, NormalizedIncomingPayload


SOURCE_TYPE_MAP = {
    "plain_text": SourceType.PLAIN_TEXT,
    "voice_message": SourceType.VOICE_MESSAGE,
    "photo": SourceType.PHOTO,
    "screenshot": SourceType.SCREENSHOT,
    "forwarded_message": SourceType.FORWARDED_MESSAGE,
    "link": SourceType.LINK,
    "document": SourceType.DOCUMENT,
    "ticket": SourceType.TICKET,
    "booking_confirmation": SourceType.BOOKING_CONFIRMATION,
    "receipt": SourceType.RECEIPT,
    "image_with_text": SourceType.IMAGE_WITH_TEXT,
    "mixed_message": SourceType.MIXED_MESSAGE,
}


class InputNormalizer:
    def normalize(self, item: IncomingItem, attachments: list[Attachment] | None = None) -> NormalizedIncomingPayload:
        source_attachments = attachments if attachments is not None else list(item.attachments)
        payload_attachments = [self._normalize_attachment(attachment) for attachment in source_attachments]
        source_type = SOURCE_TYPE_MAP.get(item.incoming_type or "", SourceType.UNKNOWN)
        if payload_attachments and item.raw_text and source_type in {SourceType.PHOTO, SourceType.DOCUMENT}:
            source_type = SourceType.MIXED_MESSAGE
        return NormalizedIncomingPayload(
            incoming_id=str(item.id),
            user_id=item.user_id,
            source_type=source_type,
            raw_text=item.raw_text,
            caption=item.original_caption,
            source_url=item.source_url,
            media_type=item.media_type,
            forwarded=bool((item.metadata_json or {}).get("forwarded")) or source_type == SourceType.FORWARDED_MESSAGE,
            original_message_id=item.original_message_id or item.telegram_message_id,
            original_chat_id=item.original_chat_id or item.telegram_chat_id,
            original_caption=item.original_caption,
            attachments=payload_attachments,
            metadata=dict(item.metadata_json or {}),
        )

    def _normalize_attachment(self, attachment: Attachment) -> NormalizedAttachment:
        return NormalizedAttachment(
            telegram_file_id=attachment.telegram_file_id,
            telegram_unique_file_id=attachment.telegram_unique_file_id,
            file_name=attachment.file_name,
            mime_type=attachment.mime_type,
            media_type=attachment.content_type,
            local_path=attachment.local_path,
            file_size=attachment.file_size,
            width=attachment.width,
            height=attachment.height,
            duration_seconds=attachment.duration_seconds,
        )
