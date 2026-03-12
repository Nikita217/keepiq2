from __future__ import annotations

from uuid import UUID

from models import Event, ListEntity, ListItem, Note, ObjectLink, Reminder, ReplyLaterItem, SavedItem, Task
from models.enums import EventStatus, NoteStatus, ObjectType, ReminderStatus, TaskStatus
from repositories.incoming import IncomingRepository
from utils.time import now_local


class ObjectMutationService:
    def __init__(self, session) -> None:
        self.session = session
        self.incoming_repo = IncomingRepository(session)

    async def convert(
        self,
        *,
        user_id: int,
        source_type: str,
        source_id: UUID,
        target_type: str,
        title: str | None = None,
        description: str | None = None,
        scheduled_at=None,
        kind: str | None = None,
        source_url: str | None = None,
        list_items: list[str] | None = None,
    ):
        source = await self._load_source(user_id=user_id, source_type=source_type, source_id=source_id)
        values = self._extract_source_values(source_type, source)
        title = title or values["title"]
        description = description if description is not None else values["description"]
        scheduled_at = scheduled_at if scheduled_at is not None else values["scheduled_at"]
        kind = kind or values["kind"]
        source_url = source_url or values["source_url"]
        list_items = list_items if list_items else values["list_items"]

        created = await self._create_target(
            user_id=user_id,
            source_incoming_item_id=values["source_incoming_item_id"],
            target_type=target_type,
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            kind=kind,
            source_url=source_url,
            list_items=list_items,
        )
        self._archive_source(source_type, source)

        if values["source_incoming_item_id"]:
            await self.incoming_repo.add_object_link(
                ObjectLink(
                    incoming_item_id=values["source_incoming_item_id"],
                    object_type=target_type,
                    object_id=str(created.id),
                )
            )

        await self.session.commit()
        await self.session.refresh(created)
        return created

    async def _load_source(self, *, user_id: int, source_type: str, source_id: UUID):
        model = {
            "task": Task,
            "reminder": Reminder,
            "event": Event,
            "note": Note,
            "reply_later": ReplyLaterItem,
        }.get(source_type)
        if model is None:
            raise LookupError("source type is not supported")

        source = await self.session.get(model, source_id)
        if source is None or source.user_id != user_id:
            raise PermissionError("object not found")
        return source

    def _extract_source_values(self, source_type: str, source) -> dict:
        if source_type == "task":
            return {
                "title": source.title,
                "description": source.description,
                "scheduled_at": source.due_at or source.scheduled_for,
                "kind": "task",
                "source_url": None,
                "list_items": [],
                "source_incoming_item_id": source.source_incoming_item_id,
            }
        if source_type == "reminder":
            return {
                "title": source.title,
                "description": None,
                "scheduled_at": source.remind_at,
                "kind": "reminder",
                "source_url": None,
                "list_items": [],
                "source_incoming_item_id": source.source_incoming_item_id,
            }
        if source_type == "event":
            return {
                "title": source.title,
                "description": source.description,
                "scheduled_at": source.starts_at,
                "kind": "event",
                "source_url": None,
                "list_items": [],
                "source_incoming_item_id": source.source_incoming_item_id,
            }
        if source_type == "note":
            return {
                "title": source.title,
                "description": source.body,
                "scheduled_at": None,
                "kind": source.kind,
                "source_url": None,
                "list_items": [],
                "source_incoming_item_id": source.source_incoming_item_id,
            }
        if source_type == "reply_later":
            return {
                "title": source.title,
                "description": source.conversation_summary,
                "scheduled_at": source.reply_due_at,
                "kind": "reply_later",
                "source_url": None,
                "list_items": [],
                "source_incoming_item_id": source.source_incoming_item_id,
            }
        raise LookupError("source type is not supported")

    async def _create_target(
        self,
        *,
        user_id: int,
        source_incoming_item_id,
        target_type: str,
        title: str,
        description: str | None,
        scheduled_at,
        kind: str | None,
        source_url: str | None,
        list_items: list[str],
    ):
        if target_type == "task":
            target = Task(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                description=description,
                due_at=scheduled_at,
                scheduled_for=scheduled_at,
                priority="medium",
                status=self._resolve_task_status(scheduled_at),
                extra_json={},
            )
        elif target_type == "reminder":
            target = Reminder(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                remind_at=scheduled_at,
                remind_on=scheduled_at.date() if scheduled_at else None,
                status=ReminderStatus.ACTIVE.value,
                extra_json={},
            )
        elif target_type == "event":
            target = Event(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                description=description,
                starts_at=scheduled_at,
                status=EventStatus.UPCOMING.value,
                extra_json={},
            )
        elif target_type == "note":
            target = Note(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                body=description,
                kind=kind or "note",
                status=NoteStatus.ACTIVE.value,
                extra_json={},
            )
        elif target_type == "reply_later":
            target = ReplyLaterItem(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                conversation_summary=description,
                reply_due_at=scheduled_at,
                status="open",
                suggested_replies_json={},
            )
        elif target_type == "save_only":
            target = SavedItem(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                summary=description,
                source_url=source_url,
                extra_json={},
            )
        elif target_type == "list":
            target = ListEntity(
                user_id=user_id,
                source_incoming_item_id=source_incoming_item_id,
                title=title,
                description=description,
                kind=kind or "general",
                extra_json={},
            )
        else:
            raise LookupError("target type is not supported")

        self.session.add(target)
        await self.session.flush()

        if target_type == "list" and list_items:
            self.session.add_all(
                [
                    ListItem(list_id=target.id, text=item_text, sort_order=index)
                    for index, item_text in enumerate(list_items)
                    if item_text.strip()
                ]
            )
            await self.session.flush()

        return target

    def _archive_source(self, source_type: str, source) -> None:
        if source_type == "task":
            source.status = TaskStatus.ARCHIVED.value
        elif source_type == "reminder":
            source.status = ReminderStatus.CANCELLED.value
        elif source_type == "event":
            source.status = EventStatus.CANCELLED.value
        elif source_type == "note":
            source.status = NoteStatus.ARCHIVED.value
        elif source_type == "reply_later":
            source.status = "done"

    def _resolve_task_status(self, due_at) -> str:
        if due_at:
            return TaskStatus.SCHEDULED.value if due_at > now_local() else TaskStatus.ACTIVE.value
        return TaskStatus.ACTIVE.value
