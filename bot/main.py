from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

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
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router())
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())