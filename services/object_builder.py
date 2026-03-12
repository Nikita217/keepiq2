from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models import Event, ListEntity, ListItem, Note, ObjectLink, Reminder, ReplyLaterItem, SavedItem, Task
from repositories.events import EventRepository
from repositories.incoming import IncomingRepository
from repositories.lists import ListRepository
from repositories.notes import NoteRepository
from repositories.reminders import ReminderRepository
from repositories.tasks import TaskRepository
from schemas.ai import AnalysisPayload, CandidateObject


class ObjectBuilderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.incoming_repo = IncomingRepository(session)
        self.task_repo = TaskRepository(session)
        self.reminder_repo = ReminderRepository(session)
        self.event_repo = EventRepository(session)
        self.note_repo = NoteRepository(session)
        self.list_repo = ListRepository(session)

    async def materialize(self, *, user_id: int, incoming_item_id, payload: AnalysisPayload) -> list[str]:
        created: list[str] = []
        for candidate in payload.candidates:
            object_id = await self._create_candidate(
                user_id=user_id,
                incoming_item_id=incoming_item_id,
                candidate=candidate,
                payload=payload,
            )
            if object_id:
                created.append(object_id)
                await self.incoming_repo.add_object_link(
                    ObjectLink(incoming_item_id=incoming_item_id, object_type=candidate.object_type, object_id=object_id)
                )
        return created

    async def _create_candidate(self, *, user_id: int, incoming_item_id, candidate: CandidateObject, payload: AnalysisPayload) -> str | None:
        if candidate.object_type == "task":
            task = await self.task_repo.create(
                Task(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    description=candidate.description,
                    due_at=candidate.due_at,
                    scheduled_for=candidate.due_at,
                    confidence=payload.confidence,
                    category_hint=candidate.category_hint,
                )
            )
            return str(task.id)

        if candidate.object_type == "reminder":
            reminder = await self.reminder_repo.create(
                Reminder(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    remind_at=candidate.remind_at,
                    extra_json=candidate.metadata,
                )
            )
            return str(reminder.id)

        if candidate.object_type == "event":
            event = await self.event_repo.create(
                Event(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    description=candidate.description,
                    starts_at=candidate.event_at,
                    place_name=candidate.metadata.get("place_name"),
                    address=candidate.metadata.get("address"),
                    booking_reference=candidate.metadata.get("booking_reference"),
                    extra_json=candidate.metadata,
                )
            )
            return str(event.id)

        if candidate.object_type == "list":
            list_entity = await self.list_repo.create_list(
                ListEntity(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    description=candidate.description,
                    kind=candidate.metadata.get("kind", "general"),
                )
            )
            if candidate.items:
                await self.list_repo.create_items(
                    [
                        ListItem(list_id=list_entity.id, text=item_text, sort_order=index)
                        for index, item_text in enumerate(candidate.items)
                    ]
                )
            return str(list_entity.id)

        if candidate.object_type == "reply_later":
            reply_later = await self.note_repo.create_reply_later(
                ReplyLaterItem(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    conversation_summary=candidate.description,
                    reply_due_at=candidate.due_at,
                    suggested_replies_json=payload.draft_replies,
                )
            )
            return str(reply_later.id)

        if candidate.object_type == "saved":
            saved = await self.note_repo.create_saved(
                SavedItem(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    summary=candidate.description,
                    source_url=candidate.metadata.get("url"),
                    extra_json=candidate.metadata,
                )
            )
            return str(saved.id)

        note = await self.note_repo.create_note(
            Note(
                user_id=user_id,
                source_incoming_item_id=incoming_item_id,
                title=candidate.title,
                body=candidate.description,
                kind=candidate.metadata.get("kind", "note"),
                extra_json=candidate.metadata,
            )
        )
        return str(note.id)
