from __future__ import annotations

from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine

from models import Base

logger = structlog.get_logger(__name__)


def run_migrations() -> None:
    root = Path(__file__).resolve().parent.parent
    alembic_ini = root / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic_ini_missing", path=str(alembic_ini))
        return
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "head")
    logger.info("database_migrated", revision="head")


async def create_all(engine: AsyncEngine) -> None:
    run_migrations()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
