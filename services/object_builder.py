from __future__ import annotations

from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from models import Event, ListEntity, ListItem, Note, ObjectLink, Reminder, ReplyLaterItem, SavedItem, Task
from models.enums import ImportanceLevel, ReminderStatus, TaskStatus
from repositories.events import EventRepository
from repositories.incoming import IncomingRepository
from repositories.lists import ListRepository
from repositories.notes import NoteRepository
from repositories.reminders import ReminderRepository
from repositories.tasks import TaskRepository
from schemas.ai import AnalysisPayload, CandidateObject
from utils.time import now_local


class ObjectBuilderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.incoming_repo = IncomingRepository(session)
        self.task_repo = TaskRepository(session)
        self.reminder_repo = ReminderRepository(session)
        self.event_repo = EventRepository(session)
        self.note_repo = NoteRepository(session)
        self.list_repo = ListRepository(session)

    async def materialize(
        self,
        *,
        user_id: int,
        incoming_item_id,
        payload: AnalysisPayload,
        upsert: bool = False,
    ) -> list[str]:
        created: list[str] = []
        existing_links_by_type: dict[str, list[ObjectLink]] = defaultdict(list)
        used_link_ids: set[int] = set()
        linked_objects: dict[str, list[object]] = defaultdict(list)

        if upsert:
            for link in await self.incoming_repo.list_object_links(incoming_item_id):
                existing_links_by_type[link.object_type].append(link)

        for candidate in payload.candidates:
            existing_link = None
            for link in existing_links_by_type.get(candidate.object_type, []):
                if link.id not in used_link_ids:
                    existing_link = link
                    used_link_ids.add(link.id)
                    break

            obj = await self._create_or_update_candidate(
                user_id=user_id,
                incoming_item_id=incoming_item_id,
                candidate=candidate,
                payload=payload,
                existing_link=existing_link,
                linked_objects=linked_objects,
            )
            if obj is None:
                continue
            linked_objects[candidate.object_type].append(obj)
            created.append(str(obj.id))
            if existing_link is None:
                await self.incoming_repo.add_object_link(
                    ObjectLink(incoming_item_id=incoming_item_id, object_type=candidate.object_type, object_id=str(obj.id))
                )
        return created

    async def _create_or_update_candidate(
        self,
        *,
        user_id: int,
        incoming_item_id,
        candidate: CandidateObject,
        payload: AnalysisPayload,
        existing_link: ObjectLink | None,
        linked_objects: dict[str, list[object]],
    ) -> object | None:
        if candidate.object_type == "task":
            task = await self._load_existing(existing_link, Task)
            if task is None:
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
                        priority=ImportanceLevel.MEDIUM.value,
                        status=self._resolve_task_status(candidate),
                        extra_json=candidate.metadata,
                    )
                )
            else:
                task.title = candidate.title
                task.description = candidate.description
                task.due_at = candidate.due_at
                task.scheduled_for = candidate.due_at
                task.confidence = payload.confidence
                task.category_hint = candidate.category_hint
                task.status = self._resolve_task_status(candidate)
                task.extra_json = candidate.metadata
            return task

        if candidate.object_type == "reminder":
            reminder = await self._load_existing(existing_link, Reminder)
            linked_to = candidate.metadata.get("linked_to")
            task_id = None
            event_id = None
            if linked_to == "event" and linked_objects.get("event"):
                event_id = linked_objects["event"][0].id
            elif linked_to == "task" and linked_objects.get("task"):
                task_id = linked_objects["task"][0].id
            elif linked_objects.get("event"):
                event_id = linked_objects["event"][0].id
            elif linked_objects.get("task"):
                task_id = linked_objects["task"][0].id

            if reminder is None:
                reminder = await self.reminder_repo.create(
                    Reminder(
                        user_id=user_id,
                        source_incoming_item_id=incoming_item_id,
                        task_id=task_id,
                        event_id=event_id,
                        title=candidate.title,
                        remind_at=candidate.remind_at,
                        remind_on=candidate.remind_at.date() if candidate.remind_at else None,
                        status=ReminderStatus.ACTIVE.value,
                        extra_json=candidate.metadata,
                    )
                )
            else:
                reminder.task_id = task_id or reminder.task_id
                reminder.event_id = event_id or reminder.event_id
                reminder.title = candidate.title
                reminder.remind_at = candidate.remind_at
                reminder.remind_on = candidate.remind_at.date() if candidate.remind_at else None
                reminder.extra_json = candidate.metadata
            return reminder

        if candidate.object_type == "event":
            event = await self._load_existing(existing_link, Event)
            if event is None:
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
            else:
                event.title = candidate.title
                event.description = candidate.description
                event.starts_at = candidate.event_at
                event.place_name = candidate.metadata.get("place_name")
                event.address = candidate.metadata.get("address")
                event.booking_reference = candidate.metadata.get("booking_reference")
                event.extra_json = candidate.metadata
            return event

        if candidate.object_type == "list":
            list_entity = await self._load_existing(existing_link, ListEntity)
            if list_entity is None:
                list_entity = await self.list_repo.create_list(
                    ListEntity(
                        user_id=user_id,
                        source_incoming_item_id=incoming_item_id,
                        title=candidate.title,
                        description=candidate.description,
                        kind=candidate.metadata.get("kind", "general"),
                        extra_json=candidate.metadata,
                    )
                )
            else:
                list_entity.title = candidate.title
                list_entity.description = candidate.description
                list_entity.kind = candidate.metadata.get("kind", "general")
                list_entity.extra_json = candidate.metadata
                await self.session.execute(delete(ListItem).where(ListItem.list_id == list_entity.id))
            if candidate.items:
                await self.list_repo.create_items(
                    [
                        ListItem(list_id=list_entity.id, text=item_text, sort_order=index)
                        for index, item_text in enumerate(candidate.items)
                    ]
                )
            return list_entity

        if candidate.object_type == "reply_later":
            reply_later = await self._load_existing(existing_link, ReplyLaterItem)
            if reply_later is None:
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
            else:
                reply_later.title = candidate.title
                reply_later.conversation_summary = candidate.description
                reply_later.reply_due_at = candidate.due_at
                reply_later.suggested_replies_json = payload.draft_replies
            return reply_later

        if candidate.object_type == "saved":
            saved = await self._load_existing(existing_link, SavedItem)
            if saved is None:
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
            else:
                saved.title = candidate.title
                saved.summary = candidate.description
                saved.source_url = candidate.metadata.get("url")
                saved.extra_json = candidate.metadata
            return saved

        note = await self._load_existing(existing_link, Note)
        kind = candidate.metadata.get("kind", "note")
        if note is None:
            note = await self.note_repo.create_note(
                Note(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=candidate.title,
                    body=candidate.description,
                    kind=kind,
                    extra_json=candidate.metadata,
                )
            )
        else:
            note.title = candidate.title
            note.body = candidate.description
            note.kind = kind
            note.extra_json = candidate.metadata
        return note

    async def _load_existing(self, existing_link: ObjectLink | None, model):
        if existing_link is None:
            return None
        try:
            object_id = UUID(existing_link.object_id)
        except (TypeError, ValueError):
            object_id = existing_link.object_id
        return await self.session.get(model, object_id)

    def _resolve_task_status(self, candidate: CandidateObject) -> str:
        if candidate.due_at:
            return TaskStatus.SCHEDULED.value if candidate.due_at > now_local() else TaskStatus.ACTIVE.value
        return TaskStatus.INBOX.value
