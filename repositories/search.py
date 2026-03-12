from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Event, IncomingItem, ListEntity, Note, ReplyLaterItem, SavedItem, Task
from repositories.base import BaseRepository
from schemas.search import SearchRequest, SearchResultItem


class SearchRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(self, user_id: int, request: SearchRequest) -> list[SearchResultItem]:
        q = f"%{request.q}%"
        results: list[SearchResultItem] = []

        task_stmt = select(Task).where(Task.user_id == user_id).where(or_(Task.title.ilike(q), Task.description.ilike(q)))
        for task in await self.fetch_all(task_stmt):
            results.append(
                SearchResultItem(
                    object_type="task",
                    object_id=task.id,
                    title=task.title,
                    snippet=task.description,
                    status=task.status,
                    source_incoming_item_id=task.source_incoming_item_id,
                )
            )

        note_stmt = select(Note).where(Note.user_id == user_id).where(or_(Note.title.ilike(q), Note.body.ilike(q)))
        for note in await self.fetch_all(note_stmt):
            results.append(
                SearchResultItem(
                    object_type="note",
                    object_id=note.id,
                    title=note.title,
                    snippet=note.body,
                    status=note.status,
                    source_incoming_item_id=note.source_incoming_item_id,
                )
            )

        incoming_stmt = (
            select(IncomingItem)
            .where(IncomingItem.user_id == user_id)
            .where(
                or_(
                    IncomingItem.raw_text.ilike(q),
                    IncomingItem.transcript_text.ilike(q),
                    IncomingItem.ocr_text.ilike(q),
                    IncomingItem.summary.ilike(q),
                )
            )
        )
        for item in await self.fetch_all(incoming_stmt):
            results.append(
                SearchResultItem(
                    object_type="incoming",
                    object_id=item.id,
                    title=item.summary or item.proposed_type or "Incoming item",
                    snippet=item.raw_text or item.transcript_text or item.ocr_text,
                    status=item.parse_status,
                    source_incoming_item_id=item.id,
                )
            )

        event_stmt = (
            select(Event)
            .where(Event.user_id == user_id)
            .where(or_(Event.title.ilike(q), Event.description.ilike(q), Event.place_name.ilike(q)))
        )
        for event in await self.fetch_all(event_stmt):
            results.append(
                SearchResultItem(
                    object_type="event",
                    object_id=event.id,
                    title=event.title,
                    snippet=event.description or event.place_name,
                    status=event.status,
                    source_incoming_item_id=event.source_incoming_item_id,
                )
            )

        list_stmt = select(ListEntity).where(ListEntity.user_id == user_id).where(ListEntity.title.ilike(q))
        for item in await self.fetch_all(list_stmt):
            results.append(
                SearchResultItem(
                    object_type="list",
                    object_id=item.id,
                    title=item.title,
                    snippet=item.description,
                    source_incoming_item_id=item.source_incoming_item_id,
                )
            )

        reply_stmt = (
            select(ReplyLaterItem)
            .where(ReplyLaterItem.user_id == user_id)
            .where(or_(ReplyLaterItem.title.ilike(q), ReplyLaterItem.conversation_summary.ilike(q)))
        )
        for item in await self.fetch_all(reply_stmt):
            results.append(
                SearchResultItem(
                    object_type="reply_later",
                    object_id=item.id,
                    title=item.title,
                    snippet=item.conversation_summary,
                    status=item.status,
                    source_incoming_item_id=item.source_incoming_item_id,
                )
            )

        saved_stmt = (
            select(SavedItem)
            .where(SavedItem.user_id == user_id)
            .where(or_(SavedItem.title.ilike(q), SavedItem.summary.ilike(q), SavedItem.source_url.ilike(q)))
        )
        for item in await self.fetch_all(saved_stmt):
            results.append(
                SearchResultItem(
                    object_type="saved",
                    object_id=item.id,
                    title=item.title,
                    snippet=item.summary or item.source_url,
                    source_incoming_item_id=item.source_incoming_item_id,
                )
            )

        return results
