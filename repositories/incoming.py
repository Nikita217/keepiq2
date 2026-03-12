from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import AIAnalysisResult, Attachment, IncomingItem, ObjectLink, ParsedEntity, ProcessingLog
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
            )
        )
        return await self.fetch_one(stmt)

    async def list_inbox(self, user_id: int, limit: int = 50) -> list[IncomingItem]:
        stmt = (
            select(IncomingItem)
            .where(IncomingItem.user_id == user_id)
            .order_by(desc(IncomingItem.created_at))
            .limit(limit)
            .options(
                selectinload(IncomingItem.attachments),
                selectinload(IncomingItem.entities),
                selectinload(IncomingItem.processing_logs),
            )
        )
        return await self.fetch_all(stmt)

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
