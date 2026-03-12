from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.users import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def ensure_user(
        self,
        telegram_user_id: int,
        first_name: str | None,
        username: str | None,
        last_name: str | None = None,
        language_code: str | None = None,
    ):
        user = await self.repo.get_or_create(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            language_code=language_code,
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user
