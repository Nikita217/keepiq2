from __future__ import annotations

from datetime import datetime

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Event
from repositories.base import BaseRepository


class EventRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, event: Event) -> Event:
        self.session.add(event)
        await self.flush()
        return event

    async def upcoming(self, user_id: int, from_dt: datetime) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.user_id == user_id)
            .where(Event.status == "upcoming")
            .where(Event.starts_at >= from_dt)
            .order_by(asc(Event.starts_at))
        )
        return await self.fetch_all(stmt)

    async def list_all(self, user_id: int) -> list[Event]:
        return await self.fetch_all(select(Event).where(Event.user_id == user_id).order_by(asc(Event.starts_at)))
