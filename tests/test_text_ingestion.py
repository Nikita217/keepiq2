from __future__ import annotations

from ai.heuristic_provider import HeuristicAIProvider
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
