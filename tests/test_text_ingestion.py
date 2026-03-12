from __future__ import annotations

from sqlalchemy import select

from ai.heuristic_provider import HeuristicAIProvider
from models import ListEntity, Reminder, Task
from services.ingestion import IngestionService
from storage.local import LocalStorageAdapter


class DummyStorage(LocalStorageAdapter):
    pass


async def test_reminder_text_creates_reviewable_item(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="напомни завтра позвонить Ване",
    )
    assert item.proposed_type == "reminder"
    assert item.summary
    reminders = (await session.execute(select(Reminder))).scalars().all()
    tasks = (await session.execute(select(Task))).scalars().all()
    assert reminders
    assert tasks


async def test_shopping_text_becomes_list(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="купить батарейки, корм и шампунь",
    )
    assert item.proposed_type == "list"
    lists = (await session.execute(select(ListEntity))).scalars().all()
    assert lists


async def test_explicit_task_materializes_task(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="отправить документы Диме сегодня вечером",
    )
    assert item.proposed_type == "task"
    tasks = (await session.execute(select(Task))).scalars().all()
    assert tasks