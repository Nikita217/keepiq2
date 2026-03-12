from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

from ai.base import AIProvider
from models import AIAnalysisResult, Attachment, IncomingItem, ParsedEntity, ProcessingLog
from models.enums import IncomingType, ParseStatus
from repositories.incoming import IncomingRepository
from services.analysis import AnalysisService
from services.object_builder import ObjectBuilderService
from storage.base import StorageAdapter
from utils.time import now_local
from utils.text import compact_text


AUTO_CREATE_TYPES = {"task", "reminder", "event", "list", "reply_later", "note", "saved"}
TEXT_DOCUMENT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".yaml", ".yml"}


class IngestionService:
    def __init__(self, session, *, provider: AIProvider, storage: StorageAdapter) -> None:
        self.session = session
        self.repo = IncomingRepository(session)
        self.analysis = AnalysisService(provider)
        self.object_builder = ObjectBuilderService(session)
        self.storage = storage

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
        incoming_type = IncomingType.FORWARDED.value if forwarded else IncomingType.TEXT.value
        if text.strip().startswith("http://") or text.strip().startswith("https://"):
            incoming_type = IncomingType.LINK.value

        item = IncomingItem(
            user_id=user_id,
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            telegram_update_id=update_id,
            incoming_type=incoming_type,
            raw_text=text,
            source_url=text if incoming_type == IncomingType.LINK.value else None,
            metadata_json={
                "forwarded": forwarded,
                "source_signature": self._build_text_signature(text),
            },
            parse_status=ParseStatus.PROCESSING.value,
        )
        await self.repo.create(item)
        await self.repo.add_log(ProcessingLog(incoming_item_id=item.id, stage="ingest", message="Text accepted"))
        await self._analyze_and_materialize(item, forwarded=forwarded)
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

        item = IncomingItem(
            user_id=user_id,
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            telegram_update_id=update_id,
            incoming_type=incoming_type,
            raw_text=raw_text,
            metadata_json=metadata_json,
            parse_status=ParseStatus.PROCESSING.value,
        )
        await self.repo.create(item)

        saved_path = await self.storage.save_bytes(user_id=user_id, filename=filename, content=content)
        await self.repo.add_attachment(
            Attachment(
                incoming_item_id=item.id,
                telegram_file_id=telegram_file_id,
                telegram_unique_file_id=telegram_unique_file_id,
                file_name=filename,
                mime_type=content_type,
                content_type=content_type,
                local_path=str(saved_path),
                file_size=len(content),
            )
        )
        if incoming_type in {IncomingType.DOCUMENT.value, IncomingType.TICKET.value, IncomingType.BOOKING.value}:
            item.ocr_text = self._extract_document_text(filename=filename, content_type=content_type, content=content)
        await self.repo.add_log(ProcessingLog(incoming_item_id=item.id, stage="storage", message=f"Saved {filename}"))
        await self._analyze_and_materialize(
            item,
            file_path=saved_path,
            file_name=filename,
            mime_type=content_type,
            forwarded=forwarded,
        )
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def _analyze_and_materialize(
        self,
        item: IncomingItem,
        *,
        file_path: Path | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        forwarded: bool = False,
    ) -> None:
        transcript = item.transcript_text
        ocr_text = item.ocr_text

        if item.incoming_type in {IncomingType.VOICE.value, IncomingType.AUDIO.value} and file_path:
            transcript = await self.analysis.transcribe_audio(file_path)
            item.transcript_text = transcript
            await self.repo.add_log(ProcessingLog(incoming_item_id=item.id, stage="transcription", message="Audio transcribed"))

        payload = await self.analysis.analyze_incoming(
            incoming_type=item.incoming_type,
            raw_text=item.raw_text,
            transcript_text=transcript,
            ocr_text=ocr_text,
            file_path=file_path,
            file_name=file_name,
            mime_type=mime_type,
            metadata=item.metadata_json,
            forwarded=forwarded,
        )
        if payload.proposed_type == "saved" and item.source_url:
            domain = urlparse(item.source_url).netloc
            payload.summary = payload.summary or f"Ссылка сохранена: {domain}"

        metadata_json = dict(item.metadata_json or {})
        metadata_json.update(
            {
                "assistant_response": payload.assistant_response,
                "clarification_question": payload.clarification_question,
                "analysis_provider": payload.provider,
                "suggested_actions": [action.model_dump(mode="json") for action in payload.suggested_actions],
            }
        )
        item.metadata_json = metadata_json
        item.summary = payload.summary
        item.proposed_type = payload.proposed_type
        item.confidence = payload.confidence
        item.needs_confirmation = payload.needs_confirmation
        item.processed_at = now_local()
        item.parse_status = ParseStatus.NEEDS_REVIEW.value if payload.needs_confirmation else ParseStatus.CONFIRMED.value
        await self.repo.add_analysis(
            AIAnalysisResult(
                incoming_item_id=item.id,
                provider=payload.provider,
                model=payload.model,
                prompt_version="v3",
                summary=payload.summary,
                proposed_type=payload.proposed_type,
                confidence=payload.confidence,
                result_json=payload.model_dump(mode="json"),
                fallback_used=payload.provider != "openai",
            )
        )
        for entity in payload.extracted_entities:
            await self.repo.add_entity(
                ParsedEntity(
                    incoming_item_id=item.id,
                    entity_type=entity.entity_type,
                    value=entity.value,
                    normalized_value=entity.normalized_value,
                    confidence=entity.confidence,
                    source=payload.provider,
                )
            )
        if payload.proposed_type == "reply_later" and not payload.draft_replies:
            source_text = item.raw_text or transcript or ocr_text or payload.summary
            payload.draft_replies = await self.analysis.provider.generate_reply_drafts(source_text)
        if self._should_materialize(payload):
            await self.object_builder.materialize(user_id=item.user_id, incoming_item_id=item.id, payload=payload, upsert=True)
        await self.repo.add_log(
            ProcessingLog(
                incoming_item_id=item.id,
                stage="analysis",
                message=f"Analyzed as {payload.proposed_type}",
                payload_json=payload.model_dump(mode="json"),
            )
        )

    def _should_materialize(self, payload: AIAnalysisResult | object) -> bool:
        if getattr(payload, "proposed_type", None) == "answer":
            return False
        if getattr(payload, "needs_confirmation", True):
            return False
        if getattr(payload, "proposed_type", None) in AUTO_CREATE_TYPES and getattr(payload, "confidence", 0) >= 0.72:
            return True
        return getattr(payload, "confidence", 0) >= 0.82

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

    def _build_text_signature(self, text: str) -> str:
        return hashlib.sha1(compact_text(text).encode("utf-8")).hexdigest()

    def _build_file_signature(self, *, filename: str, content: bytes, telegram_unique_file_id: str | None) -> str:
        if telegram_unique_file_id:
            return telegram_unique_file_id
        digest = hashlib.sha1()
        digest.update(filename.encode("utf-8", errors="ignore"))
        digest.update(content[:2048])
        return digest.hexdigest()
