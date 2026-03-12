from __future__ import annotations

from sqlalchemy import select

from ai.heuristic_provider import HeuristicAIProvider
from models import ListEntity, Reminder, Task
from services.ingestion import IngestionService
from services.inbox_actions import InboxActionService
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
    assert reminders[0].task_id == tasks[0].id
    assert reminders[0].remind_on is not None


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


async def test_question_text_generates_answer(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="Что мне сделать с этой заметкой?",
    )
    assert item.proposed_type == "answer"
    assert item.metadata_json.get("assistant_response")
    tasks = (await session.execute(select(Task))).scalars().all()
    assert not tasks


async def test_manual_resolve_reuses_existing_task(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="отправить документы Диме сегодня вечером",
    )
    before = (await session.execute(select(Task))).scalars().all()
    assert len(before) == 1

    resolved = await InboxActionService(session).resolve(item_id=item.id, target_type="task")
    after = (await session.execute(select(Task))).scalars().all()
    assert len(after) == 1
    assert resolved.metadata_json.get("resolved_object_type") == "task"
