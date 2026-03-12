from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Note, ReplyLaterItem, SavedItem
from models.enums import NoteStatus
from repositories.base import BaseRepository


class NoteRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_note(self, note: Note) -> Note:
        self.session.add(note)
        await self.flush()
        return note

    async def create_reply_later(self, reply_later: ReplyLaterItem) -> ReplyLaterItem:
        self.session.add(reply_later)
        await self.flush()
        return reply_later

    async def create_saved(self, saved_item: SavedItem) -> SavedItem:
        self.session.add(saved_item)
        await self.flush()
        return saved_item

    async def list_notes(self, user_id: int, limit: int = 50) -> list[Note]:
        stmt = (
            select(Note)
            .where(Note.user_id == user_id)
            .where(Note.status == NoteStatus.ACTIVE.value)
            .order_by(desc(Note.updated_at), desc(Note.created_at))
            .limit(limit)
        )
        return await self.fetch_all(stmt)

    async def list_reply_later(self, user_id: int, limit: int = 50) -> list[ReplyLaterItem]:
        stmt = (
            select(ReplyLaterItem)
            .where(ReplyLaterItem.user_id == user_id)
            .where(ReplyLaterItem.status == "open")
            .order_by(desc(ReplyLaterItem.updated_at), desc(ReplyLaterItem.created_at))
            .limit(limit)
        )
        return await self.fetch_all(stmt)

    async def list_saved(self, user_id: int, limit: int = 50) -> list[SavedItem]:
        stmt = (
            select(SavedItem)
            .where(SavedItem.user_id == user_id)
            .order_by(desc(SavedItem.updated_at), desc(SavedItem.created_at))
            .limit(limit)
        )
        return await self.fetch_all(stmt)
