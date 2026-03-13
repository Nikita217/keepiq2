from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from domain.action_models import ActionSuggestion
from domain.entity_models import EntityDraft
from domain.enums import FinalType
from models import Event, ListEntity, ListItem, Note, ObjectLink, Reminder
from models.enums import EventStatus, NoteStatus, ObjectType, ReminderStatus
from repositories.events import EventRepository
from repositories.incoming import IncomingRepository
from repositories.lists import ListRepository
from repositories.notes import NoteRepository
from repositories.reminders import ReminderRepository


class ObjectBuilderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.incoming_repo = IncomingRepository(session)
        self.reminder_repo = ReminderRepository(session)
        self.event_repo = EventRepository(session)
        self.note_repo = NoteRepository(session)
        self.list_repo = ListRepository(session)

    async def materialize_drafts(
        self,
        *,
        user_id: int,
        incoming_item_id,
        drafts: list[EntityDraft],
        upsert: bool = False,
    ) -> list[ObjectLink]:
        created_links: list[ObjectLink] = []
        existing_links_by_type: dict[str, list[ObjectLink]] = defaultdict(list)
        used_link_ids: set[int] = set()
        if upsert:
            for link in await self.incoming_repo.list_object_links(incoming_item_id):
                existing_links_by_type[link.object_type].append(link)

        for draft in drafts:
            if draft.type == FinalType.REMINDER:
                _, link = await self._create_or_update_reminder(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    draft=draft,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.REMINDER.value, used_link_ids),
                )
            elif draft.type == FinalType.EVENT:
                _, link = await self._create_or_update_event(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    draft=draft,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.EVENT.value, used_link_ids),
                )
            elif draft.type == FinalType.LIST:
                _, link = await self._create_or_update_list(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    draft=draft,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.LIST.value, used_link_ids),
                )
            else:
                _, link = await self._create_or_update_note(
                    user_id=user_id,
                    incoming_item_id=incoming_item_id,
                    draft=draft,
                    existing_link=self._take_link(existing_links_by_type, ObjectType.NOTE.value, used_link_ids),
                )
            if link is not None:
                created_links.append(link)
        return created_links

    async def materialize_action(
        self,
        *,
        user_id: int,
        incoming_item_id,
        action: ActionSuggestion,
        upsert: bool = True,
    ) -> list[ObjectLink]:
        return await self.materialize_drafts(
            user_id=user_id,
            incoming_item_id=incoming_item_id,
            drafts=action.items,
            upsert=upsert,
        )

    def _take_link(self, existing_links_by_type: dict[str, list[ObjectLink]], object_type: str, used_link_ids: set[int]) -> ObjectLink | None:
        for link in existing_links_by_type.get(object_type, []):
            if link.id not in used_link_ids:
                used_link_ids.add(link.id)
                return link
        return None

    async def _create_or_update_event(self, *, user_id: int, incoming_item_id, draft: EntityDraft, existing_link: ObjectLink | None):
        event = await self._load_existing(existing_link, Event)
        starts_at = draft.scheduled_at
        if event is None:
            event = await self.event_repo.create(
                Event(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=draft.title,
                    description=draft.description,
                    starts_at=starts_at,
                    status=EventStatus.UPCOMING.value,
                    extra_json=draft.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.EVENT.value, object_id=str(event.id))
            )
            return event, link
        event.title = draft.title
        event.description = draft.description
        event.starts_at = starts_at
        event.extra_json = draft.metadata
        return event, None

    async def _create_or_update_reminder(self, *, user_id: int, incoming_item_id, draft: EntityDraft, existing_link: ObjectLink | None):
        reminder = await self._load_existing(existing_link, Reminder)
        remind_at = draft.scheduled_at
        remind_on = draft.scheduled_date or (remind_at.date() if remind_at else None)
        if reminder is None:
            reminder = await self.reminder_repo.create(
                Reminder(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=draft.title,
                    remind_at=remind_at,
                    remind_on=remind_on,
                    status=ReminderStatus.ACTIVE.value,
                    extra_json=draft.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.REMINDER.value, object_id=str(reminder.id))
            )
            return reminder, link
        reminder.title = draft.title
        reminder.remind_at = remind_at
        reminder.remind_on = remind_on
        reminder.extra_json = draft.metadata
        return reminder, None

    async def _create_or_update_note(self, *, user_id: int, incoming_item_id, draft: EntityDraft, existing_link: ObjectLink | None):
        note = await self._load_existing(existing_link, Note)
        if note is None:
            note = await self.note_repo.create_note(
                Note(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=draft.title,
                    body=draft.description,
                    kind=draft.metadata.get("kind", "note"),
                    status=NoteStatus.ACTIVE.value,
                    extra_json=draft.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.NOTE.value, object_id=str(note.id))
            )
            return note, link
        note.title = draft.title
        note.body = draft.description
        note.kind = draft.metadata.get("kind", "note")
        note.extra_json = draft.metadata
        return note, None

    async def _create_or_update_list(self, *, user_id: int, incoming_item_id, draft: EntityDraft, existing_link: ObjectLink | None):
        list_entity = await self._load_existing(existing_link, ListEntity)
        if list_entity is None:
            list_entity = await self.list_repo.create_list(
                ListEntity(
                    user_id=user_id,
                    source_incoming_item_id=incoming_item_id,
                    title=draft.title,
                    description=draft.description,
                    kind=draft.metadata.get("kind", "general"),
                    extra_json=draft.metadata,
                )
            )
            link = await self.incoming_repo.add_object_link(
                ObjectLink(incoming_item_id=incoming_item_id, object_type=ObjectType.LIST.value, object_id=str(list_entity.id))
            )
        else:
            list_entity.title = draft.title
            list_entity.description = draft.description
            list_entity.kind = draft.metadata.get("kind", "general")
            list_entity.extra_json = draft.metadata
            await self.session.execute(delete(ListItem).where(ListItem.list_id == list_entity.id))
            link = None
        if draft.list_items:
            await self.list_repo.create_items(
                [ListItem(list_id=list_entity.id, text=text, sort_order=index) for index, text in enumerate(draft.list_items)]
            )
        return list_entity, link

    async def _load_existing(self, existing_link: ObjectLink | None, model):
        if existing_link is None:
            return None
        try:
            object_id = UUID(existing_link.object_id)
        except (TypeError, ValueError):
            object_id = existing_link.object_id
        return await self.session.get(model, object_id)
