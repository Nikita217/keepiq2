from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import DailyDigestSettings, User, UserSettings
from repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        return await self.fetch_one(select(User).where(User.telegram_user_id == telegram_user_id))

    async def get_or_create(
        self,
        telegram_user_id: int,
        first_name: str | None,
        username: str | None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_user_id)
        if user:
            user.first_name = first_name
            user.username = username
            user.last_name = last_name
            user.language_code = language_code
            return user

        user = User(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            language_code=language_code,
        )
        self.session.add(user)
        await self.flush()
        self.session.add(UserSettings(user_id=user.id, timezone="Europe/Moscow"))
        self.session.add(DailyDigestSettings(user_id=user.id))
        await self.flush()
        return user
