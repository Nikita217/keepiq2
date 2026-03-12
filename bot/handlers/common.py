from __future__ import annotations

from uuid import UUID

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.callbacks import InboxCallback
from db.session import SessionLocal
from models import IncomingItem
from models.enums import ParseStatus
from schemas.ai import AnalysisPayload, CandidateObject
from services.object_builder import ObjectBuilderService
from services.reminders import ReminderService

router = Router()


@router.callback_query(InboxCallback.filter(F.action == "confirm"))
async def confirm_inbox_item(callback: CallbackQuery, callback_data: InboxCallback) -> None:
    async with SessionLocal() as session:
        item = await session.get(IncomingItem, UUID(callback_data.item_id))
        if item is None:
            await callback.answer("Объект не найден", show_alert=True)
            return
        item.needs_confirmation = False
        item.parse_status = ParseStatus.CONFIRMED.value
        await session.commit()
    await callback.answer("Подтверждено")


@router.callback_query(InboxCallback.filter(F.action == "save_as"))
async def save_as(callback: CallbackQuery, callback_data: InboxCallback) -> None:
    async with SessionLocal() as session:
        item = await session.get(IncomingItem, UUID(callback_data.item_id))
        if item is None:
            await callback.answer("Объект не найден", show_alert=True)
            return
        payload = AnalysisPayload(
            provider="manual",
            summary=item.summary or item.raw_text or "Manual save",
            proposed_type=callback_data.target,
            confidence=1.0,
            needs_confirmation=False,
            candidates=[
                CandidateObject(
                    object_type=callback_data.target,
                    title=(item.summary or item.raw_text or callback_data.target)[:100],
                    description=item.raw_text or item.transcript_text or item.ocr_text or item.summary,
                )
            ],
            draft_replies={},
            raw={"manual": True},
        )
        await ObjectBuilderService(session).materialize(user_id=item.user_id, incoming_item_id=item.id, payload=payload)
        item.needs_confirmation = False
        item.parse_status = ParseStatus.CONFIRMED.value
        await session.commit()
    await callback.answer("Сохранено")


@router.callback_query(F.data.startswith("reminder:done:"))
async def reminder_done(callback: CallbackQuery) -> None:
    reminder_id = UUID(callback.data.split(":")[2])
    async with SessionLocal() as session:
        await ReminderService(session).complete(reminder_id)
    await callback.answer("Готово")


@router.callback_query(F.data.startswith("reminder:snooze:"))
async def reminder_snooze(callback: CallbackQuery) -> None:
    _, _, reminder_id, minutes = callback.data.split(":")
    async with SessionLocal() as session:
        await ReminderService(session).snooze(UUID(reminder_id), minutes=int(minutes))
    await callback.answer("Отложено")
