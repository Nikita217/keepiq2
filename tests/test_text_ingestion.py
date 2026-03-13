from __future__ import annotations

from sqlalchemy import select

from ai.heuristic_provider import HeuristicAIProvider
from models import Attachment, Event, ListEntity, Note, Reminder
from repositories.incoming import IncomingRepository
from services.ingestion import IngestionService
from services.inbox_actions import InboxActionService
from storage.local import LocalStorageAdapter


class DummyStorage(LocalStorageAdapter):
    pass


class VoiceFixtureProvider(HeuristicAIProvider):
    def __init__(self, transcript: str) -> None:
        super().__init__()
        self.transcript = transcript

    async def transcribe_audio(self, file_path):
        return self.transcript


async def test_motivation_does_not_become_extra_entity(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="Я хочу накачаться, поэтому напомни мне завтра покачать пресс",
    )

    assert item.proposed_type == "reminder"
    assert len(item.analysis_result_json["items"]) == 1
    assert "покачать пресс" in item.analysis_result_json["items"][0]["title"].lower()
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == [
        "Напомнить завтра в 10:00",
        "Напомнить завтра в 12:00",
        "Напомнить завтра в 18:00",
        "Оставить во входящих",
    ]


async def test_shopping_list_is_one_list(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=2,
        update_id=2,
        text="Купить молоко, сыр, батарейки",
    )

    assert item.proposed_type == "list"
    assert len(item.analysis_result_json["items"]) == 1
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == ["Сохранить списком", "Сохранить заметкой", "Оставить во входящих"]
    lists = (await session.execute(select(ListEntity))).scalars().all()
    assert len(lists) == 1
    assert lists[0].title == "Список покупок"


async def test_event_context_creates_one_reminder(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=3,
        update_id=3,
        text="18 мая концерт The Hatters, напомни за неделю купить билет",
    )

    assert item.proposed_type == "reminder"
    assert len(item.analysis_result_json["items"]) == 1
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == [
        "Напомнить 11 мая в 10:00",
        "Напомнить 11 мая в 12:00",
        "Напомнить 11 мая в 18:00",
        "Оставить во входящих",
    ]


async def test_idea_becomes_note(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=4,
        update_id=4,
        text="Идея: снять ролик про старые нейросети",
    )

    assert item.proposed_type == "note"
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == ["Сохранить заметкой", "Оставить во входящих"]
    notes = (await session.execute(select(Note))).scalars().all()
    assert len(notes) == 1


async def test_two_independent_actions_are_allowed(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=5,
        update_id=5,
        text="Завтра купить корм и написать Диме",
    )

    assert item.proposed_type == "reminder"
    assert len(item.analysis_result_json["items"]) == 2


async def test_screenshot_without_action_stays_note_like(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=6,
        update_id=6,
        incoming_type="screenshot",
        filename="chat.png",
        content=b"png",
        content_type="image/png",
        metadata={"ocr_text": "Скрин переписки про детали встречи и цены без явной просьбы"},
    )

    assert item.proposed_type == "note"
    assert all(action["label"] != "Напомнить" for action in item.metadata_json.get("suggested_actions", []))


async def test_ticket_event_is_materialized_with_exact_time(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=7,
        update_id=7,
        incoming_type="ticket",
        filename="ticket.pdf",
        content=b"pdf",
        content_type="application/pdf",
        metadata={"ocr_text": "Билет: концерт The Hatters 18 мая 2026 в 19:00, VK Stadium"},
    )

    assert item.proposed_type == "event"
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels[:2] == ["Создать событие 18 мая в 19:00", "Создать событие 18 мая"]
    events = (await session.execute(select(Event))).scalars().all()
    assert len(events) == 1
    assert events[0].starts_at is not None


async def test_bad_ocr_goes_to_inbox_but_keeps_original(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=8,
        update_id=8,
        incoming_type="screenshot",
        filename="bad.png",
        content=b"png",
        content_type="image/png",
        metadata={"ocr_text": ""},
    )

    assert item.parse_status == "needs_review"
    attachments = (await session.execute(select(Attachment))).scalars().all()
    assert attachments


async def test_voice_with_one_action_and_emotion_stays_one_reminder(session):
    provider = VoiceFixtureProvider("Я переживаю, что забуду, напомни завтра оплатить интернет")
    service = IngestionService(session, provider=provider, storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=9,
        update_id=9,
        incoming_type="voice_message",
        filename="voice.ogg",
        content=b"voice",
        content_type="audio/ogg",
    )

    assert item.proposed_type == "reminder"
    assert len(item.analysis_result_json["items"]) == 1


async def test_voice_with_multiple_actions_splits(session):
    provider = VoiceFixtureProvider("Завтра купить корм и написать Диме")
    service = IngestionService(session, provider=provider, storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=10,
        update_id=10,
        incoming_type="voice_message",
        filename="voice.ogg",
        content=b"voice",
        content_type="audio/ogg",
    )

    assert len(item.analysis_result_json["items"]) == 2


async def test_date_without_time_offers_ready_times(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=11,
        update_id=11,
        text="18 мая концерт The Hatters",
    )

    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == [
        "Создать событие 18 мая",
        "Создать событие 18 мая в 10:00",
        "Создать событие 18 мая в 18:00",
        "Оставить во входящих",
    ]
    assert all("выбрать" not in label.lower() for label in labels)


async def test_absent_date_does_not_create_fake_reminder(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=12,
        update_id=12,
        text="Напомни купить батарейки",
    )

    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == ["Сохранить заметкой", "Оставить во входящих"]
    reminders = (await session.execute(select(Reminder))).scalars().all()
    assert reminders == []


async def test_resolve_action_creates_object_and_removes_from_inbox(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=13,
        update_id=13,
        text="Я хочу накачаться, поэтому напомни мне завтра покачать пресс",
    )

    await InboxActionService(session).resolve(item_id=item.id, user_id=1, suggested_action_id=0)
    reminders = (await session.execute(select(Reminder))).scalars().all()
    assert len(reminders) == 1
    inbox_items = await IncomingRepository(session).list_inbox(user_id=1)
    assert all(inbox_item.id != item.id for inbox_item in inbox_items)
