from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from models import DailyDigestSettings, IncomingItem, Reminder, User
from utils.settings import get_settings


class TelegramNotificationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.bot = Bot(token=self.settings.bot_token)

    async def send_reminder(self, user: User, reminder: Reminder, source: IncomingItem | None = None) -> None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Готово", callback_data=f"reminder:done:{reminder.id}")],
                [InlineKeyboardButton(text="Отложить 30 мин", callback_data=f"reminder:snooze:{reminder.id}:30")],
                [InlineKeyboardButton(text="Открыть Mini App", url=self.settings.mini_app_public_url or self.settings.mini_app_dev_url)],
            ]
        )
        text = f"Напоминание: {reminder.title}"
        if source and source.summary:
            text += f"\nИсточник: {source.summary[:180]}"
        await self.bot.send_message(user.telegram_user_id, text, reply_markup=keyboard)

    async def send_digest(self, user: User, digest_settings: DailyDigestSettings, title: str, lines: list[str]) -> None:
        text = title + "\n" + "\n".join(f"• {line}" for line in lines)
        await self.bot.send_message(user.telegram_user_id, text)
