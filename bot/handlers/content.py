from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from ai.factory import build_ai_provider
from bot.keyboards import inbox_actions
from db.session import SessionLocal
from models.enums import IncomingType
from services.ingestion import IngestionService
from services.users import UserService
from storage.local import LocalStorageAdapter

router = Router()
provider = build_ai_provider()
storage = LocalStorageAdapter()


async def _ensure_user(message: Message):
    async with SessionLocal() as session:
        return await UserService(session).ensure_user(
            telegram_user_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )


async def _reply_with_result(message: Message, item) -> None:
    summary = item.summary or item.raw_text or item.transcript_text or item.ocr_text or "Сохранено"
    text = (
        f"Сохранено во входящие.\n"
        f"AI думает: {item.proposed_type or 'unknown'}\n"
        f"Уверенность: {round((item.confidence or 0) * 100)}%\n"
        f"Кратко: {summary[:220]}"
    )
    await message.answer(text, reply_markup=inbox_actions(str(item.id)))


@router.message(F.text)
async def handle_text(message: Message) -> None:
    user = await _ensure_user(message)
    async with SessionLocal() as session:
        service = IngestionService(session, provider=provider, storage=storage)
        item = await service.ingest_text(
            user_id=user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            update_id=None,
            text=message.text,
            forwarded=bool(message.forward_origin),
        )
    await _reply_with_result(message, item)


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    user = await _ensure_user(message)
    voice = message.voice
    file = await message.bot.get_file(voice.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read()
    async with SessionLocal() as session:
        service = IngestionService(session, provider=provider, storage=storage)
        item = await service.ingest_file(
            user_id=user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            update_id=None,
            incoming_type=IncomingType.VOICE.value,
            filename=f"voice-{voice.file_unique_id}.ogg",
            content=content,
            content_type="voice",
            telegram_file_id=voice.file_id,
            telegram_unique_file_id=voice.file_unique_id,
            metadata={"duration": voice.duration},
        )
    await _reply_with_result(message, item)


@router.message(F.audio)
async def handle_audio(message: Message) -> None:
    user = await _ensure_user(message)
    audio = message.audio
    file = await message.bot.get_file(audio.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read()
    async with SessionLocal() as session:
        service = IngestionService(session, provider=provider, storage=storage)
        item = await service.ingest_file(
            user_id=user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            update_id=None,
            incoming_type=IncomingType.AUDIO.value,
            filename=audio.file_name or f"audio-{audio.file_unique_id}.mp3",
            content=content,
            content_type="audio",
            telegram_file_id=audio.file_id,
            telegram_unique_file_id=audio.file_unique_id,
            metadata={"duration": audio.duration, "title": audio.title},
        )
    await _reply_with_result(message, item)


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    user = await _ensure_user(message)
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read()
    incoming_type = IncomingType.SCREENSHOT.value if (message.caption or "").lower().find("скрин") >= 0 else IncomingType.PHOTO.value
    async with SessionLocal() as session:
        service = IngestionService(session, provider=provider, storage=storage)
        item = await service.ingest_file(
            user_id=user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            update_id=None,
            incoming_type=incoming_type,
            filename=f"photo-{photo.file_unique_id}.jpg",
            content=content,
            content_type="image",
            telegram_file_id=photo.file_id,
            telegram_unique_file_id=photo.file_unique_id,
            metadata={"caption": message.caption},
        )
    await _reply_with_result(message, item)


@router.message(F.document)
async def handle_document(message: Message) -> None:
    user = await _ensure_user(message)
    document = message.document
    file = await message.bot.get_file(document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read()
    lower_name = (document.file_name or "").lower()
    incoming_type = IncomingType.DOCUMENT.value
    if any(keyword in lower_name for keyword in ["ticket", "билет", "booking", "бронь"]):
        incoming_type = IncomingType.TICKET.value
    async with SessionLocal() as session:
        service = IngestionService(session, provider=provider, storage=storage)
        item = await service.ingest_file(
            user_id=user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            update_id=None,
            incoming_type=incoming_type,
            filename=document.file_name or f"document-{document.file_unique_id}",
            content=content,
            content_type=document.mime_type or "document",
            telegram_file_id=document.file_id,
            telegram_unique_file_id=document.file_unique_id,
            metadata={"caption": message.caption, "mime_type": document.mime_type},
        )
    await _reply_with_result(message, item)
