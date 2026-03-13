from __future__ import annotations

from sqlalchemy import select

from ai.heuristic_provider import HeuristicAIProvider
from models import Event, ListEntity, Note, Reminder
from services.ingestion import IngestionService
from storage.local import LocalStorageAdapter


class DummyStorage(LocalStorageAdapter):
    pass


class VoiceFixtureProvider(HeuristicAIProvider):
    def __init__(self, transcript: str) -> None:
        super().__init__()
        self.transcript = transcript

    async def transcribe_audio(self, file_path):
        return self.transcript


class BadVoiceProvider(HeuristicAIProvider):
    async def transcribe_audio(self, file_path):
        return "[transcription unavailable] voice.ogg"


async def test_tomorrow_buy_slippers_builds_reminder_suggestions(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=1,
        update_id=1,
        text="завтра купить тапки",
    )

    assert item.proposed_type == "reminder"
    assert item.needs_confirmation is True
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels[:4] == ["Завтра в 12:00", "Завтра в 15:00", "Завтра в 18:00", "Просто сохранить"]
    assert "Понял" in item.metadata_json["assistant_response"]


async def test_shopping_list_becomes_list(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=2,
        update_id=2,
        text="купить молоко, сыр, батарейки",
    )

    assert item.proposed_type == "list"
    lists = (await session.execute(select(ListEntity))).scalars().all()
    assert len(lists) == 1
    assert lists[0].title == "Список покупок"


async def test_voice_with_two_reminders_and_one_note_is_split(session):
    provider = VoiceFixtureProvider(
        "написать Саше, купить батарейки, идея для видео про старые нейросети"
    )
    service = IngestionService(session, provider=provider, storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=3,
        update_id=3,
        incoming_type="voice_message",
        filename="voice.ogg",
        content=b"voice",
        content_type="audio/ogg",
    )

    result_items = item.analysis_result_json["items"]
    assert len(result_items) == 3
    assert sum(1 for analysis_item in result_items if analysis_item["type"] == "reminder") == 2
    assert sum(1 for analysis_item in result_items if analysis_item["type"] == "note") == 1
    assert "Разобрал это" in item.metadata_json["assistant_response"]


async def test_chat_screenshot_request_becomes_reminder(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=4,
        update_id=4,
        incoming_type="screenshot",
        filename="chat.png",
        content=b"png",
        content_type="image/png",
        metadata={"ocr_text": "Скрин чата: можешь завтра отправить договор?"},
    )

    assert item.proposed_type == "reminder"


async def test_chat_screenshot_reply_later_becomes_reminder(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=5,
        update_id=5,
        incoming_type="screenshot",
        filename="chat.png",
        content=b"png",
        content_type="image/png",
        metadata={"ocr_text": "Скрин переписки: ответить Маше вечером"},
    )

    assert item.proposed_type == "reminder"
    reminder_items = (await session.execute(select(Reminder))).scalars().all()
    assert reminder_items


async def test_ticket_becomes_event_with_reminder_options(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=6,
        update_id=6,
        incoming_type="ticket",
        filename="ticket.pdf",
        content=b"pdf",
        content_type="application/pdf",
        metadata={"ocr_text": "Билет: концерт The Hatters 18 мая 2026 в 19:00, VK Stadium"},
    )

    assert item.proposed_type == "event"
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels[:4] == ["За день", "За 3 часа", "Утром в день события", "Сохранить событие"]


async def test_useful_screenshot_without_action_becomes_note(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=8,
        update_id=8,
        incoming_type="screenshot",
        filename="reference.png",
        content=b"png",
        content_type="image/png",
        metadata={"ocr_text": "Подборка референсов для лендинга с хорошей типографикой"},
    )

    assert item.proposed_type == "note"
    notes = (await session.execute(select(Note))).scalars().all()
    assert notes


async def test_unknown_object_goes_to_inbox_review(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=9,
        update_id=9,
        incoming_type="photo",
        filename="meme.png",
        content=b"png",
        content_type="image/png",
    )

    assert item.proposed_type == "inbox_review"
    assert item.needs_confirmation is True
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert labels == ["Это напоминание", "Это список", "Это событие", "Это заметка"]


async def test_date_without_time_stays_ambiguous_for_event(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=10,
        update_id=10,
        text="18 мая концерт The Hatters",
    )

    assert item.proposed_type == "event"
    assert item.needs_confirmation is True
    labels = [action["label"] for action in item.metadata_json.get("suggested_actions", [])]
    assert "Утром в этот день" in labels


async def test_time_without_date_does_not_create_exact_datetime_for_reminder(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=11,
        update_id=11,
        text="купить цветы в 19:00",
    )

    assert item.proposed_type == "reminder"
    assert item.needs_confirmation is True
    assert item.analysis_result_json["items"][0]["datetime"] is None


async def test_bad_ocr_routes_to_inbox(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=12,
        update_id=12,
        incoming_type="screenshot",
        filename="empty.png",
        content=b"png",
        content_type="image/png",
        metadata={"ocr_text": ""},
    )

    assert item.proposed_type == "inbox_review"


async def test_bad_transcription_routes_to_inbox(session):
    service = IngestionService(session, provider=BadVoiceProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=13,
        update_id=13,
        incoming_type="voice_message",
        filename="voice.ogg",
        content=b"voice",
        content_type="audio/ogg",
    )

    assert item.proposed_type == "inbox_review"


async def test_forwarded_message_with_comment_becomes_reminder(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=15,
        update_id=15,
        text="Пересланное сообщение: ответить Саше позже",
        forwarded=True,
    )

    assert item.proposed_type == "reminder"


async def test_idea_becomes_note(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=16,
        update_id=16,
        text="Идея для видео: коты делают бизнес в Египте",
    )

    assert item.proposed_type == "note"
    notes = (await session.execute(select(Note))).scalars().all()
    assert notes


async def test_poorly_classified_text_falls_back_to_inbox_review(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=17,
        update_id=17,
        text="ммм ну вот это такое",
    )

    assert item.proposed_type == "inbox_review"


async def test_high_confidence_reminder_is_materialized(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_text(
        user_id=1,
        chat_id=1,
        message_id=18,
        update_id=18,
        text="купить шапку",
    )

    assert item.proposed_type == "reminder"
    reminders = (await session.execute(select(Reminder))).scalars().all()
    assert reminders


async def test_ticket_event_materializes_event(session):
    service = IngestionService(session, provider=HeuristicAIProvider(), storage=DummyStorage())
    item = await service.ingest_file(
        user_id=1,
        chat_id=1,
        message_id=19,
        update_id=19,
        incoming_type="ticket",
        filename="ticket.pdf",
        content=b"pdf",
        content_type="application/pdf",
        metadata={"ocr_text": "Билет: концерт The Hatters 18 мая 2026 в 19:00"},
    )

    events = (await session.execute(select(Event))).scalars().all()
    assert item.proposed_type == "event"
    assert events

