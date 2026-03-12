from __future__ import annotations

from datetime import date

from repositories.events import EventRepository
from repositories.incoming import IncomingRepository
from repositories.lists import ListRepository
from repositories.notes import NoteRepository
from repositories.reminders import ReminderRepository
from repositories.tasks import TaskRepository


class DashboardService:
    def __init__(self, session) -> None:
        self.tasks = TaskRepository(session)
        self.reminders = ReminderRepository(session)
        self.events = EventRepository(session)
        self.incoming = IncomingRepository(session)
        self.notes = NoteRepository(session)
        self.lists = ListRepository(session)

    async def overview(self, user_id: int, today: date) -> dict:
        tasks = await self.tasks.list_all(user_id)
        reminders = await self.reminders.list_for_date(user_id, today)
        events = await self.events.list_all(user_id)
        inbox = await self.incoming.list_inbox(user_id, limit=20)
        notes = await self.notes.list_notes(user_id, limit=10)
        lists = await self.lists.list_lists(user_id, limit=10)
        reply_later = await self.notes.list_reply_later(user_id, limit=50)
        return {
            "today": {
                "tasks": len([task for task in tasks if task.status in {"active", "scheduled", "waiting_reply", "inbox"}]),
                "reminders": len(reminders),
                "events": len([event for event in events if event.starts_at]),
            },
            "counters": {
                "inbox": len([item for item in inbox if item.needs_confirmation]),
                "overdue": len([task for task in tasks if task.due_at and task.status not in {"done", "archived"}]),
                "reply_later": len(reply_later),
                "notes": len(notes),
                "lists": len(lists),
            },
            "soon_events": [
                {"id": str(event.id), "title": event.title, "starts_at": event.starts_at.isoformat() if event.starts_at else None}
                for event in events[:5]
            ],
            "pending_inbox": [
                {"id": str(item.id), "summary": item.summary, "proposed_type": item.proposed_type, "confidence": item.confidence}
                for item in inbox[:8]
            ],
        }
