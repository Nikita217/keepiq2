from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import AIAnalysisResult, Attachment, IncomingItem, ObjectLink, ParsedEntity, ProcessingLog
from models.enums import ParseStatus
from repositories.base import BaseRepository


class IncomingRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, item: IncomingItem) -> IncomingItem:
        self.session.add(item)
        await self.flush()
        return item

    async def get(self, item_id: UUID) -> IncomingItem | None:
        stmt = (
            select(IncomingItem)
            .where(IncomingItem.id == item_id)
            .options(
                selectinload(IncomingItem.attachments),
                selectinload(IncomingItem.entities),
                selectinload(IncomingItem.processing_logs),
                selectinload(IncomingItem.object_links),
                selectinload(IncomingItem.analysis_results),
            )
        )
        return await self.fetch_one(stmt)

    async def list_inbox(self, user_id: int, limit: int = 50) -> list[IncomingItem]:
        stmt = (
            select(IncomingItem)
            .where(IncomingItem.user_id == user_id)
            .where(IncomingItem.parse_status.in_([ParseStatus.NEW.value, ParseStatus.PROCESSING.value, ParseStatus.NEEDS_REVIEW.value]))
            .order_by(desc(IncomingItem.needs_confirmation), desc(IncomingItem.created_at))
            .limit(limit)
            .options(
                selectinload(IncomingItem.attachments),
                selectinload(IncomingItem.entities),
                selectinload(IncomingItem.processing_logs),
                selectinload(IncomingItem.object_links),
                selectinload(IncomingItem.analysis_results),
            )
        )
        return await self.fetch_all(stmt)

    async def list_object_links(self, incoming_item_id: UUID) -> list[ObjectLink]:
        stmt = select(ObjectLink).where(ObjectLink.incoming_item_id == incoming_item_id).order_by(ObjectLink.id.asc())
        return await self.fetch_all(stmt)

    async def get_latest_analysis(self, incoming_item_id: UUID) -> AIAnalysisResult | None:
        stmt = (
            select(AIAnalysisResult)
            .where(AIAnalysisResult.incoming_item_id == incoming_item_id)
            .order_by(AIAnalysisResult.id.desc())
            .limit(1)
        )
        return await self.fetch_one(stmt)

    async def add_attachment(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.flush()
        return attachment

    async def add_entity(self, entity: ParsedEntity) -> ParsedEntity:
        self.session.add(entity)
        await self.flush()
        return entity

    async def add_analysis(self, analysis: AIAnalysisResult) -> AIAnalysisResult:
        self.session.add(analysis)
        await self.flush()
        return analysis

    async def add_log(self, log: ProcessingLog) -> ProcessingLog:
        self.session.add(log)
        await self.flush()
        return log

    async def add_object_link(self, link: ObjectLink) -> ObjectLink:
        self.session.add(link)
        await self.flush()
        return link
