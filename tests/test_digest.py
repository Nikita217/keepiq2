from __future__ import annotations

from datetime import date

from ai.heuristic_provider import HeuristicAIProvider
from services.digests import DigestService
from services.ingestion import IngestionService
from storage.local import LocalStorageAdapter


class DummyStorage(LocalStorageAdapter):
    pass


async def test_digest_contains_inbox_counter(session):
    ingestion = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    await ingestion.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="сохранить эту мысль на потом",
    )
    digest = await DigestService(session).build_morning_digest(1, date.today())
    assert any("Ждут разбора" in line for line in digest.lines)
