from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.keyboards import mini_app_menu_button
from bot.router import build_router
from db.bootstrap import create_all
from db.session import engine
from utils.logging import configure_logging
from utils.settings import get_settings


async def main() -> None:
    settings = get_settings()
    configure_logging()
    await create_all(engine)
    bot = Bot(token=settings.bot_token)
    mini_app_url = settings.mini_app_public_url or settings.mini_app_dev_url
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить KeepIQ"),
            BotCommand(command="open", description="Открыть Mini App"),
            BotCommand(command="inbox", description="Показать входящие"),
            BotCommand(command="today", description="Показать сегодня"),
        ]
    )
    await bot.set_chat_menu_button(menu_button=mini_app_menu_button(mini_app_url))
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router())
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
