from __future__ import annotations

from sqlalchemy import select

from ai.heuristic_provider import HeuristicAIProvider
from models import ListEntity, Reminder, Task
from services.ingestion import IngestionService
from services.inbox_actions import InboxActionService
from storage.local import LocalStorageAdapter


class DummyStorage(LocalStorageAdapter):
    pass


async def test_reminder_text_creates_suggestions_before_materialization(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="напомни завтра позвонить Ване",
    )
    assert item.proposed_type == "reminder"
    assert item.metadata_json.get("suggested_actions")
    reminders = (await session.execute(select(Reminder))).scalars().all()
    tasks = (await session.execute(select(Task))).scalars().all()
    assert not reminders
    assert not tasks

    resolved = await InboxActionService(session).resolve(item_id=item.id, suggested_action_id=1)
    reminders = (await session.execute(select(Reminder))).scalars().all()
    tasks = (await session.execute(select(Task))).scalars().all()
    assert reminders
    assert tasks
    assert reminders[0].task_id == tasks[0].id
    assert reminders[0].remind_on is not None
    assert resolved.metadata_json.get("last_selected_action")


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


async def test_explicit_task_gets_adaptive_suggestions(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="купить шапку",
    )
    assert item.proposed_type == "task"
    assert item.needs_confirmation is True
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels
    assert labels[0] == "Добавить задачу"
    assert any("Сегодня" in label or "Завтра" in label for label in labels[1:])


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
    await InboxActionService(session).resolve(item_id=item.id, suggested_action_id=0)
    before = (await session.execute(select(Task))).scalars().all()
    assert len(before) == 1

    resolved = await InboxActionService(session).resolve(item_id=item.id, suggested_action_id=0)
    after = (await session.execute(select(Task))).scalars().all()
    assert len(after) == 1
    assert resolved.metadata_json.get("resolved_object_type") == "task"
