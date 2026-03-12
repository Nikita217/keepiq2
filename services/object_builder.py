from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from domain.enums import IntentType, SuggestionActionType
from domain.models import AnalysisItem, StructuredAnalysisResult, StructuredAnalysisSuggestion
from models import Event, ListEntity, ListItem, Note, ObjectLink, Reminder, ReplyLaterItem, SavedItem, Task
from models.enums import ImportanceLevel, ObjectType, ReminderStatus, TaskStatus
from repositories.events import EventRepository
from repositories.incoming import IncomingRepository
from repositories.lists import ListRepository
from repositories.notes import NoteRepository
from repositories.reminders import ReminderRepository
from repositories.tasks import TaskRepository
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
        result: StructuredAnalysisResult,
        selected_suggestion: StructuredAnalysisSuggestion | None = None,
        upsert: bool = False,
    ) -> list[ObjectLink]:
        created_links: list[ObjectLink] = []
        existing_links_by_type: dict[str, list[ObjectLink]] = defaultdict(list)
        used_link_ids: set[int] = set()
        created_objects: dict[str, object] = {}

        if upsert:
            for link in await self.incoming_repo.list_object_links(incoming_item_id):
                existing_links_by_type[link.object_type].append(link)

        items = self._resolve_items(result, selected_suggestion)
        task_like_items = [item for item in items if item.type == IntentType.TASK]
        event_like_items = [item for item in items if item.type == IntentType.EVENT]

        for item in task_like_items:
            task, link = await self._create_or_update_task(
                user_id=user_id,
                incoming_item_id=incoming_item_id,
                item=item,
                existing_link=self._take_link(existing_links_by_type, ObjectType.TASK.value, used_link_ids),
            )
            created_objects[ObjectType.TASK.value] = task
            if link is not None:
                created_links.append(link)

        for item in event_like_items:
            event, link = await self._create_or_update_event(
                user_id=user_id,
                incoming_item_id=incoming_item_id,
                item=item,
                existing_link=self._take_link(existing_links_by_type, ObjectType.EVENT.value, used_link_ids),
            )
            created_objects[ObjectType.EVENT.value] = event
            if link is not None:
                created_links.append(link)

        for item in items:
            if item.type == IntentType.REMINDER:
                reminder, link = await self._create_or_update_reminder(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=item,
                    task_id=getattr(created_objects.get(ObjectType.TASK.value), "id", None),
                    event_id=getattr(created_objects.get(ObjectType.EVENT.value), "id", None),
                    existing_link=self._take_link(existing_links_by_type, ObjectType.REMINDER.value, used_link_ids),
                )
                if link is not None:
                    created_links.append(link)
            elif item.type == IntentType.LIST:
                list_entity, link = await self._create_or_update_list(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=item,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.LIST.value, used_link_ids),
                )
                created_objects[ObjectType.LIST.value] = list_entity
                if link is not None:
                    created_links.append(link)
            elif item.type == IntentType.NOTE:
                note, link = await self._create_or_update_note(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=item,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.NOTE.value, used_link_ids),
                )
                created_objects[ObjectType.NOTE.value] = note
                if link is not None:
                    created_links.append(link)
            elif item.type == IntentType.REPLY_LATER:
                reply_later, link = await self._create_or_update_reply_later(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=item,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.REPLY_LATER.value, used_link_ids),
                )
                created_objects[ObjectType.REPLY_LATER.value] = reply_later
                if link is not None:
                    created_links.append(link)
            elif item.type == IntentType.SAVE_ONLY:
                saved, link = await self._create_or_update_saved(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=item,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.SAVE_ONLY.value, used_link_ids),
                )
                created_objects[ObjectType.SAVE_ONLY.value] = saved
                if link is not None:
                    created_links.append(link)

        if selected_suggestion and selected_suggestion.action == SuggestionActionType.CREATE_REMINDER:
            target_item = self._target_item(result, selected_suggestion)
            if target_item and target_item.type == IntentType.TASK:
                reminder_item = AnalysisItem(
                    type=IntentType.REMINDER,
                    title=target_item.title,
                    description=target_item.description,
                    datetime=selected_suggestion.scheduled_for,
                    date_only=False,
                    category=target_item.category,
                    metadata={"auto_from_task": True},
                )
                reminder, link = await self._create_or_update_reminder(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=reminder_item,
                    task_id=getattr(created_objects.get(ObjectType.TASK.value), "id", None),
                    event_id=getattr(created_objects.get(ObjectType.EVENT.value), "id", None),
                    existing_link=self._take_link(existing_links_by_type, ObjectType.REMINDER.value, used_link_ids),
                )
                if link is not None:
                    created_links.append(link)
            elif target_item and target_item.type == IntentType.EVENT:
                reminder_item = AnalysisItem(
                    type=IntentType.REMINDER,
                    title=target_item.title,
                    description=target_item.description,
                    datetime=selected_suggestion.scheduled_for,
                    date_only=False,
                    category=target_item.category,
                    metadata={"auto_from_event": True},
                )
                reminder, link = await self._create_or_update_reminder(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    item=reminder_item,
                    task_id=None,
                    event_id=getattr(created_objects.get(ObjectType.EVENT.value), "id", None),
                    existing_link=self._take_link(existing_links_by_type, ObjectType.REMINDER.value, used_link_ids),
                )
                if link is not None:
                    created_links.append(link)

        return created_links

    def _resolve_items(
        self,
        result: StructuredAnalysisResult,
        selected_suggestion: StructuredAnalysisSuggestion | None,
    ) -> list[AnalysisItem]:
        items = list(result.items)
        if not selected_suggestion:
            return items
        if selected_suggestion.action == SuggestionActionType.KEEP_ONLY_TASKS:
            return [item for item in items if item.type == IntentType.TASK]
        if selected_suggestion.action == SuggestionActionType.CREATE_REPLY_LATER and selected_suggestion.target_item_index is not None:
            target = self._target_item(result, selected_suggestion)
            if target:
                target.type = IntentType.REPLY_LATER
                target.datetime = selected_suggestion.scheduled_for or target.datetime
            return [target] if target else items
        if selected_suggestion.action == SuggestionActionType.CREATE_LIST and selected_suggestion.target_item_index is not None:
            target = self._target_item(result, selected_suggestion)
            if target:
                target.type = IntentType.LIST
            return [target] if target else items
        return items

    def _target_item(
        self,
        result: StructuredAnalysisResult,
        selected_suggestion: StructuredAnalysisSuggestion,
    ) -> AnalysisItem | None:
        if selected_suggestion.target_item_index is None:
            return result.items[0] if result.items else None
        if 0 <= selected_suggestion.target_item_index < len(result.items):
            return result.items[selected_suggestion.target_item_index]
        return None

    def _take_link(
        self,
        existing_links_by_type: dict[str, list[ObjectLink]],
        object_type: str,
        used_link_ids: set[int],
    ) -> ObjectLink | None:
        for link in existing_links_by_type.get(object_type, []):
            if link.id not in used_link_ids:
                used_link_ids.add(link.id)
                return link
        return None

    async def _create_or_update_task(self, *, user_id: int, incoming_item_id, item: AnalysisItem, existing_link: ObjectLink | None):
        task = await self._load_existing(existing_link, Task)
        due_at = item.datetime
        if task is None:
            task = await self.task_repo.create(
                Task(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=item.title,
                    description=item.description,
                    due_at=due_at,
                    scheduled_for=due_at,
                    confidence=None,
                    category_hint=item.category,
                    priority=item.priority or ImportanceLevel.MEDIUM.value,
                    status=self._resolve_task_status(due_at),
                    extra_json=item.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.TASK.value, object_id=str(task.id))
            )
            return task, link
        task.title = item.title
        task.description = item.description
        task.due_at = due_at
        task.scheduled_for = due_at
        task.category_hint = item.category
        task.priority = item.priority or ImportanceLevel.MEDIUM.value
        task.status = self._resolve_task_status(due_at)
        task.extra_json = item.metadata
        return task, None

    async def _create_or_update_event(self, *, user_id: int, incoming_item_id, item: AnalysisItem, existing_link: ObjectLink | None):
        event = await self._load_existing(existing_link, Event)
        if event is None:
            event = await self.event_repo.create(
                Event(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=item.title,
                    description=item.description,
                    starts_at=item.datetime,
                    place_name=(item.places[0] if item.places else None),
                    extra_json=item.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.EVENT.value, object_id=str(event.id))
            )
            return event, link
        event.title = item.title
        event.description = item.description
        event.starts_at = item.datetime
        event.place_name = item.places[0] if item.places else None
        event.extra_json = item.metadata
        return event, None

    async def _create_or_update_reminder(
        self,
        *,
        user_id: int,
        incoming_item_id,
        item: AnalysisItem,
        task_id,
        event_id,
        existing_link: ObjectLink | None,
    ):
        reminder = await self._load_existing(existing_link, Reminder)
        if reminder is None:
            reminder = await self.reminder_repo.create(
                Reminder(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    task_id=task_id,
                    event_id=event_id,
                    title=item.title,
                    remind_at=item.datetime,
                    remind_on=item.datetime.date() if item.datetime else None,
                    status=ReminderStatus.ACTIVE.value,
                    extra_json=item.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.REMINDER.value, object_id=str(reminder.id))
            )
            return reminder, link
        reminder.task_id = task_id or reminder.task_id
        reminder.event_id = event_id or reminder.event_id
        reminder.title = item.title
        reminder.remind_at = item.datetime
        reminder.remind_on = item.datetime.date() if item.datetime else None
        reminder.extra_json = item.metadata
        return reminder, None

    async def _create_or_update_list(self, *, user_id: int, incoming_item_id, item: AnalysisItem, existing_link: ObjectLink | None):
        list_entity = await self._load_existing(existing_link, ListEntity)
        if list_entity is None:
            list_entity = await self.list_repo.create_list(
                ListEntity(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=item.title,
                    description=item.description,
                    kind=item.metadata.get("kind", item.category or "general"),
                    extra_json=item.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.LIST.value, object_id=str(list_entity.id))
            )
        else:
            list_entity.title = item.title
            list_entity.description = item.description
            list_entity.kind = item.metadata.get("kind", item.category or "general")
            list_entity.extra_json = item.metadata
            await self.session.execute(delete(ListItem).where(ListItem.list_id == list_entity.id))
            link = None
        if item.list_items:
            await self.list_repo.create_items(
                [ListItem(list_id=list_entity.id, text=text, sort_order=index) for index, text in enumerate(item.list_items)]
            )
        return list_entity, link

    async def _create_or_update_note(self, *, user_id: int, incoming_item_id, item: AnalysisItem, existing_link: ObjectLink | None):
        note = await self._load_existing(existing_link, Note)
        if note is None:
            note = await self.note_repo.create_note(
                Note(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=item.title,
                    body=item.description,
                    kind=item.category or item.metadata.get("kind", "note"),
                    extra_json=item.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.NOTE.value, object_id=str(note.id))
            )
            return note, link
        note.title = item.title
        note.body = item.description
        note.kind = item.category or item.metadata.get("kind", "note")
        note.extra_json = item.metadata
        return note, None

    async def _create_or_update_reply_later(self, *, user_id: int, incoming_item_id, item: AnalysisItem, existing_link: ObjectLink | None):
        reply_later = await self._load_existing(existing_link, ReplyLaterItem)
        if reply_later is None:
            reply_later = await self.note_repo.create_reply_later(
                ReplyLaterItem(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=item.title,
                    conversation_summary=item.description,
                    suggested_replies_json=item.metadata.get("draft_replies", {}),
                    reply_due_at=item.datetime,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(
                    incoming_item_id=incoming_item_id,
                    object_type=ObjectType.REPLY_LATER.value,
                    object_id=str(reply_later.id),
                )
            )
            return reply_later, link
        reply_later.title = item.title
        reply_later.conversation_summary = item.description
        reply_later.suggested_replies_json = item.metadata.get("draft_replies", {})
        reply_later.reply_due_at = item.datetime
        return reply_later, None

    async def _create_or_update_saved(self, *, user_id: int, incoming_item_id, item: AnalysisItem, existing_link: ObjectLink | None):
        saved = await self._load_existing(existing_link, SavedItem)
        if saved is None:
            saved = await self.note_repo.create_saved(
                SavedItem(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=item.title,
                    summary=item.description,
                    source_url=(item.links[0] if item.links else item.metadata.get("url")),
                    extra_json=item.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.SAVE_ONLY.value, object_id=str(saved.id))
            )
            return saved, link
        saved.title = item.title
        saved.summary = item.description
        saved.source_url = item.links[0] if item.links else item.metadata.get("url")
        saved.extra_json = item.metadata
        return saved, None

    async def _load_existing(self, existing_link: ObjectLink | None, model):
        if existing_link is None:
            return None
        try:
            object_id = UUID(existing_link.object_id)
        except (TypeError, ValueError):
            object_id = existing_link.object_id
        return await self.session.get(model, object_id)

    def _resolve_task_status(self, due_at: datetime | None) -> str:
        if due_at:
            return TaskStatus.SCHEDULED.value if due_at > now_local() else TaskStatus.ACTIVE.value
        return TaskStatus.INBOX.value

