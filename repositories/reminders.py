from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import asc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Reminder
from repositories.base import BaseRepository


class ReminderRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, reminder: Reminder) -> Reminder:
        self.session.add(reminder)
        await self.flush()
        return reminder

    async def due_reminders(self, now: datetime) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(Reminder.status.in_(["active", "snoozed"]))
            .where(Reminder.sent_at.is_(None))
            .where(or_(Reminder.remind_at <= now, Reminder.snoozed_until <= now))
            .order_by(asc(Reminder.remind_at))
        )
        return await self.fetch_all(stmt)

    async def list_for_date(self, user_id: int, day: date) -> list[Reminder]:
        stmt = select(Reminder).where(Reminder.user_id == user_id).where(Reminder.remind_on == day)
        return await self.fetch_all(stmt)

    async def list_all(self, user_id: int) -> list[Reminder]:
        return await self.fetch_all(select(Reminder).where(Reminder.user_id == user_id).order_by(asc(Reminder.remind_at)))
