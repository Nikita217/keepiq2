from __future__ import annotations

from ai.heuristic_provider import HeuristicAIProvider
from schemas.search import SearchRequest
from services.ingestion import IngestionService
from services.search import SearchService
from storage.local import LocalStorageAdapter


class DummyStorage(LocalStorageAdapter):
    pass


async def test_search_finds_raw_incoming_text(session):
    ingestion = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    await ingestion.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="идея для ролика: коты делают бизнес в Египте",
    )
    response = await SearchService(session).search(1, SearchRequest(q="Египте"))
    assert response.items
