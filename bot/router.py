from aiogram import Router

from bot.handlers.commands import router as commands_router
from bot.handlers.common import router as common_router
from bot.handlers.content import router as content_router



def build_router() -> Router:
    router = Router()
    router.include_router(commands_router)
    router.include_router(common_router)
    router.include_router(content_router)
    return router
