from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models import Base, DailyDigestSettings, User, UserSettings


@pytest.fixture()
async def session() -> AsyncIterator:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = User(id=1, telegram_user_id=1, first_name="Test", username="test")
        session.add(user)
        await session.flush()
        session.add(UserSettings(user_id=user.id, timezone="Europe/Moscow"))
        session.add(DailyDigestSettings(user_id=user.id))
        await session.commit()
        yield session
    await engine.dispose()
