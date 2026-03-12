from __future__ import annotations

import json

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from services.auth import TelegramInitDataService
from services.users import UserService


async def get_db_session(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
    x_telegram_init_data: str | None = Header(default=None),
    x_telegram_user_id: int | None = Header(default=None),
):
    user_service = UserService(session)
    if x_telegram_init_data:
        pairs = TelegramInitDataService().verify(x_telegram_init_data)
        user_payload = json.loads(pairs.get("user", "{}"))
        if not user_payload.get("id"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="telegram user missing")
        return await user_service.ensure_user(
            telegram_user_id=int(user_payload["id"]),
            first_name=user_payload.get("first_name"),
            username=user_payload.get("username"),
            last_name=user_payload.get("last_name"),
            language_code=user_payload.get("language_code"),
        )

    if x_telegram_user_id:
        return await user_service.ensure_user(
            telegram_user_id=int(x_telegram_user_id),
            first_name="Local",
            username="local-dev",
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
