from __future__ import annotations

from uuid import UUID

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from bot.callbacks import InboxCallback
from db.session import SessionLocal
from services.inbox_actions import InboxActionService
from services.reminders import ReminderService

router = Router()


async def _delete_callback_message(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None:
        return
    try:
        await message.delete()
    except TelegramBadRequest:
        # Telegram may reject deleting very old or already removed messages.
        return


@router.callback_query(InboxCallback.filter(F.action == "confirm"))
async def confirm_inbox_item(callback: CallbackQuery, callback_data: InboxCallback) -> None:
    async with SessionLocal() as session:
        try:
            item = await InboxActionService(session).resolve(item_id=UUID(callback_data.item_id))
        except LookupError:
            await callback.answer("Объект не найден", show_alert=True)
            return
    await callback.answer((item.metadata_json or {}).get("last_selected_action") or "Сохранено")
    await _delete_callback_message(callback)


@router.callback_query(InboxCallback.filter(F.action == "suggest"))
async def apply_suggested_action(callback: CallbackQuery, callback_data: InboxCallback) -> None:
    async with SessionLocal() as session:
        try:
            item = await InboxActionService(session).resolve(
                item_id=UUID(callback_data.item_id),
                suggested_action_id=int(callback_data.value or "0"),
            )
        except LookupError:
            await callback.answer("Объект не найден", show_alert=True)
            return
    await callback.answer((item.metadata_json or {}).get("last_selected_action") or "Готово")
    await _delete_callback_message(callback)


@router.callback_query(InboxCallback.filter(F.action == "save_as"))
async def save_as(callback: CallbackQuery, callback_data: InboxCallback) -> None:
    async with SessionLocal() as session:
        try:
            item = await InboxActionService(session).resolve(
                item_id=UUID(callback_data.item_id),
                target_type=callback_data.target,
            )
        except LookupError:
            await callback.answer("Объект не найден", show_alert=True)
            return
    resolved_type = item.metadata_json.get("resolved_object_type") if item.metadata_json else callback_data.target
    await callback.answer(f"Сохранено как {resolved_type}")
    await _delete_callback_message(callback)


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
