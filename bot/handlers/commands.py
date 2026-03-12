from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.keyboards import mini_app_keyboard
from db.session import SessionLocal
from models import IncomingItem, Reminder, Task
from models.enums import ParseStatus
from utils.settings import get_settings

router = Router()
settings = get_settings()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    mini_app_url = settings.mini_app_public_url or settings.mini_app_dev_url
    text = (
        "KeepIQ принимает текст, голосовые, ссылки, фото, скрины и пересланные сообщения.\n"
        "Отправь входящее как есть. Если постоянная кнопка KeepIQ внизу не открывает Mini App, нажми кнопку в этом сообщении."
    )
    await message.answer(text, reply_markup=mini_app_keyboard(mini_app_url))


@router.message(Command("open"))
async def cmd_open(message: Message) -> None:
    mini_app_url = settings.mini_app_public_url or settings.mini_app_dev_url
    await message.answer("Открой KeepIQ кнопкой ниже.", reply_markup=mini_app_keyboard(mini_app_url))


@router.message(Command("inbox"))
async def cmd_inbox(message: Message) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(IncomingItem)
            .where(IncomingItem.telegram_chat_id == message.chat.id)
            .where(IncomingItem.parse_status == ParseStatus.NEEDS_REVIEW.value)
            .order_by(IncomingItem.created_at.desc())
            .limit(5)
        )
        items = result.scalars().all()
    if not items:
        await message.answer("Inbox пуст. Всё, что пришло, уже подтверждено или ждёт следующего шага в Mini App.")
        return
    lines = [f"• {item.summary or item.raw_text or item.proposed_type} [{item.proposed_type}]" for item in items]
    await message.answer("Ждут разбора:\n" + "\n".join(lines))


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    async with SessionLocal() as session:
        tasks = (
            await session.execute(
                select(Task)
                .where(Task.user_id.in_(select(IncomingItem.user_id).where(IncomingItem.telegram_chat_id == message.chat.id)))
                .where(Task.status.in_(["active", "scheduled", "waiting_reply", "inbox"]))
                .limit(5)
            )
        ).scalars().all()
        reminders = (
            await session.execute(
                select(Reminder)
                .where(Reminder.user_id.in_(select(IncomingItem.user_id).where(IncomingItem.telegram_chat_id == message.chat.id)))
                .where(Reminder.status.in_(["active", "snoozed"]))
                .limit(5)
            )
        ).scalars().all()
    lines = ["Сегодня:"]
    lines.extend([f"Задача: {task.title}" for task in tasks] or ["Задач на сегодня пока нет"])
    lines.extend([f"Напоминание: {reminder.title}" for reminder in reminders])
    await message.answer("\n".join(lines))
