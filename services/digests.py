from __future__ import annotations

from datetime import date

from repositories.events import EventRepository
from repositories.incoming import IncomingRepository
from repositories.reminders import ReminderRepository
from repositories.tasks import TaskRepository
from schemas.digest import DigestResponse


class DigestService:
    def __init__(self, session) -> None:
        self.tasks = TaskRepository(session)
        self.reminders = ReminderRepository(session)
        self.events = EventRepository(session)
        self.incoming = IncomingRepository(session)

    async def build_morning_digest(self, user_id: int, day: date) -> DigestResponse:
        tasks = await self.tasks.list_for_today(user_id)
        reminders = await self.reminders.list_for_date(user_id, day)
        events = await self.events.list_all(user_id)
        inbox = await self.incoming.list_inbox(user_id, limit=10)
        lines = [
            f"Задачи в фокусе: {len([task for task in tasks if task.status != 'done'])}",
            f"Напоминания на сегодня: {len(reminders)}",
            f"События впереди: {len([event for event in events if event.starts_at])}",
            f"Ждут разбора: {len([item for item in inbox if item.needs_confirmation])}",
        ]
        return DigestResponse(title="Утренний обзор", lines=lines)

    async def build_evening_digest(self, user_id: int, day: date) -> DigestResponse:
        tasks = await self.tasks.list_all(user_id)
        inbox = await self.incoming.list_inbox(user_id, limit=10)
        lines = [
            f"Выполнено задач: {len([task for task in tasks if task.status == 'done'])}",
            f"Осталось в работе: {len([task for task in tasks if task.status not in {'done', 'archived'}])}",
            f"Не разобрано к вечеру: {len([item for item in inbox if item.needs_confirmation])}",
        ]
        return DigestResponse(title="Вечерний обзор", lines=lines)
