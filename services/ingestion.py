from __future__ import annotations

import hashlib
from pathlib import Path

from ai.base import AIProvider
from domain.action_models import ActionSuggestion
from models import AIAnalysisResult, Attachment, IncomingItem, ParsedEntity, ProcessingLog
from models.enums import IncomingType, ParseStatus
from repositories.incoming import IncomingRepository
from services.message_interpretation_service import MessageInterpretationService
from services.object_builder import ObjectBuilderService
from storage.base import StorageAdapter
from utils.time import now_local
from utils.text import compact_text

TEXT_DOCUMENT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".yaml", ".yml"}


class IngestionService:
    def __init__(self, session, *, provider: AIProvider, storage: StorageAdapter) -> None:
        self.session = session
        self.repo = IncomingRepository(session)
        self.interpreter = MessageInterpretationService(provider)
        self.object_builder = ObjectBuilderService(session)
        self.storage = storage
        self.provider = provider

    async def ingest_text(
        self,
        *,
        user_id: int,
        chat_id: int,
        message_id: int,
        update_id: int | None,
        text: str,
        forwarded: bool = False,
    ) -> IncomingItem:
        incoming_type = IncomingType.FORWARDED_MESSAGE.value if forwarded else IncomingType.PLAIN_TEXT.value
        if text.strip().startswith("http://") or text.strip().startswith("https://"):
            incoming_type = IncomingType.LINK.value

        item = IncomingItem(
            user_id=user_id,
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            telegram_update_id=update_id,
            original_chat_id=chat_id,
            original_message_id=message_id,
            incoming_type=incoming_type,
            raw_text=text,
            source_url=text if incoming_type == IncomingType.LINK.value else None,
            original_caption=None,
            media_type="text",
            metadata_json={
                "forwarded": forwarded,
                "source_signature": self._build_text_signature(text),
                "forwarded_text": text if forwarded else None,
            },
            parse_status=ParseStatus.PROCESSING.value,
        )
        await self.repo.create(item)
        await self.repo.add_log(ProcessingLog(incoming_item_id=item.id, stage="ingest", message="Text accepted"))
        await self._analyze_and_materialize(item, attachments=[])
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def ingest_file(
        self,
        *,
        user_id: int,
        chat_id: int,
        message_id: int,
        update_id: int | None,
        incoming_type: str,
        filename: str,
        content: bytes,
        content_type: str,
        raw_text: str | None = None,
        telegram_file_id: str | None = None,
        telegram_unique_file_id: str | None = None,
        metadata: dict | None = None,
        forwarded: bool = False,
    ) -> IncomingItem:
        metadata_json = dict(metadata or {})
        metadata_json["forwarded"] = forwarded
        metadata_json["source_signature"] = self._build_file_signature(
            filename=filename,
            content=content,
            telegram_unique_file_id=telegram_unique_file_id,
        )
        if metadata_json.get("ocr_text") is None and incoming_type in {
            IncomingType.DOCUMENT.value,
            IncomingType.TICKET.value,
            IncomingType.BOOKING_CONFIRMATION.value,
        }:
            metadata_json["ocr_text"] = self._extract_document_text(
                filename=filename,
                content_type=content_type,
                content=content,
            )

        normalized_type = self._resolve_incoming_type(
            incoming_type=incoming_type,
            raw_text=raw_text,
            content_type=content_type,
        )
        item = IncomingItem(
            user_id=user_id,
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            telegram_update_id=update_id,
            original_chat_id=chat_id,
            original_message_id=message_id,
            incoming_type=normalized_type,
            raw_text=raw_text,
            original_caption=raw_text,
            media_type=content_type,
            metadata_json=metadata_json,
            parse_status=ParseStatus.PROCESSING.value,
        )
        await self.repo.create(item)

        saved_path = await self.storage.save_bytes(user_id=user_id, filename=filename, content=content)
        attachment = Attachment(
            incoming_item_id=item.id,
            telegram_file_id=telegram_file_id,
            telegram_unique_file_id=telegram_unique_file_id,
            file_name=filename,
            mime_type=content_type,
            content_type=content_type,
            local_path=str(saved_path),
            file_size=len(content),
        )
        await self.repo.add_attachment(attachment)
        await self.repo.add_log(ProcessingLog(incoming_item_id=item.id, stage="storage", message=f"Saved {filename}"))
        await self._analyze_and_materialize(item, attachments=[attachment])
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def _analyze_and_materialize(self, item: IncomingItem, attachments: list[Attachment] | None) -> None:
        bundle = await self.interpreter.interpret(item, attachments=attachments)
        metadata_json = dict(item.metadata_json or {})
        metadata_json.update(
            {
                "assistant_response": bundle.assistant_response,
                "suggested_actions": [action.model_dump(mode="json") for action in bundle.actions],
                "source_signals": bundle.context.extracted.source_signals,
                "extraction_errors": bundle.context.extracted.extraction_errors,
            }
        )
        item.metadata_json = metadata_json
        item.extracted_text = bundle.context.extracted.extracted_text
        item.transcript_text = bundle.context.extracted.transcript
        item.ocr_text = bundle.context.extracted.ocr_text
        item.parsed_entities_json = bundle.resolved.extracted_entities.model_dump(mode="json")
        item.analysis_result_json = bundle.analysis.model_dump(mode="json")
        item.summary = bundle.resolved.summary
        item.proposed_type = bundle.resolved.primary_type.value
        item.confidence = bundle.resolved.confidence
        item.needs_confirmation = bundle.resolved.needs_user_confirmation
        item.processed_at = now_local()
        item.ai_summary = bundle.analysis.summary
        item.ai_primary_type = bundle.analysis.primary_type.value
        item.ai_secondary_candidate_type = (
            bundle.analysis.secondary_candidate_type.value if bundle.analysis.secondary_candidate_type else None
        )
        item.ai_confidence = bundle.analysis.confidence

        created_links = []
        if bundle.should_auto_create:
            created_links = await self.object_builder.materialize_drafts(
                user_id=item.user_id,
                incoming_item_id=item.id,
                drafts=bundle.drafts,
                upsert=True,
            )
            item.parse_status = ParseStatus.CONFIRMED.value
            item.needs_confirmation = False
        else:
            item.parse_status = ParseStatus.NEEDS_REVIEW.value

        item.linked_objects_json = [{"object_type": link.object_type, "object_id": link.object_id} for link in created_links]

        await self.repo.add_analysis(
            AIAnalysisResult(
                incoming_item_id=item.id,
                provider=self.provider.provider_name,
                model=getattr(self.provider, "model", None),
                prompt_version="v2",
                summary=bundle.analysis.summary,
                proposed_type=bundle.analysis.primary_type.value,
                confidence=bundle.analysis.confidence,
                result_json=bundle.analysis.model_dump(mode="json"),
                fallback_used=False,
            )
        )
        for entity in self._flatten_entities(item.id, bundle.resolved.extracted_entities.model_dump(mode="json"), bundle.resolved.confidence):
            await self.repo.add_entity(entity)
        await self.repo.add_log(
            ProcessingLog(
                incoming_item_id=item.id,
                stage="analysis",
                message=f"Analyzed as {bundle.resolved.primary_type.value}",
                payload_json={
                    "analysis": bundle.analysis.model_dump(mode="json"),
                    "resolved": bundle.resolved.model_dump(mode="json"),
                },
            )
        )

    def _flatten_entities(self, incoming_item_id, data: dict, confidence: float) -> list[ParsedEntity]:
        entities: list[ParsedEntity] = []
        for entity_type, values in data.items():
            if not values:
                continue
            for value in values:
                entities.append(
                    ParsedEntity(
                        incoming_item_id=incoming_item_id,
                        entity_type=entity_type,
                        value=str(value),
                        normalized_value=str(value),
                        confidence=confidence,
                        source=self.provider.provider_name,
                    )
                )
        return entities

    def _extract_document_text(self, *, filename: str, content_type: str, content: bytes) -> str | None:
        suffix = Path(filename).suffix.lower()
        if content_type.startswith("text/") or suffix in TEXT_DOCUMENT_EXTENSIONS:
            try:
                return compact_text(content.decode("utf-8"))[:4000]
            except UnicodeDecodeError:
                try:
                    return compact_text(content.decode("cp1251"))[:4000]
                except UnicodeDecodeError:
                    return None
        return None

    def _resolve_incoming_type(self, *, incoming_type: str, raw_text: str | None, content_type: str) -> str:
        if raw_text and incoming_type in {
            IncomingType.PHOTO.value,
            IncomingType.DOCUMENT.value,
            IncomingType.IMAGE_WITH_TEXT.value,
            IncomingType.SCREENSHOT.value,
        }:
            return IncomingType.MIXED_MESSAGE.value
        if incoming_type == IncomingType.DOCUMENT.value and content_type.startswith("image/"):
            return IncomingType.IMAGE_WITH_TEXT.value
        return incoming_type

    def _build_text_signature(self, text: str) -> str:
        return hashlib.sha1(compact_text(text).encode("utf-8")).hexdigest()

    def _build_file_signature(self, *, filename: str, content: bytes, telegram_unique_file_id: str | None) -> str:
        if telegram_unique_file_id:
            return telegram_unique_file_id
        digest = hashlib.sha1()
        digest.update(filename.encode("utf-8", errors="ignore"))
        digest.update(content[:2048])
        return digest.hexdigest()
