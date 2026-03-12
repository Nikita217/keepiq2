from __future__ import annotations

from datetime import timedelta

from sqlalchemy import update

from models import Reminder
from repositories.reminders import ReminderRepository


class ReminderService:
    def __init__(self, session) -> None:
        self.session = session
        self.repo = ReminderRepository(session)

    async def due(self, now):
        return await self.repo.due_reminders(now)

    async def complete(self, reminder_id):
        await self.session.execute(
            update(Reminder).where(Reminder.id == reminder_id).values(status="done")
        )
        await self.session.commit()

    async def snooze(self, reminder_id, *, minutes: int):
        reminder = await self.session.get(Reminder, reminder_id)
        if reminder is None:
            return
        base_dt = reminder.snoozed_until or reminder.remind_at
        if base_dt is None:
            return
        reminder.status = "snoozed"
        reminder.snoozed_until = base_dt + timedelta(minutes=minutes)
        reminder.sent_at = None
        await self.session.commit()
