from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import NullPool

from models import Base
from utils.settings import get_settings

logger = structlog.get_logger(__name__)
REQUIRED_AI_PIPELINE_COLUMNS = {
    "original_chat_id",
    "original_message_id",
    "extracted_text",
    "original_caption",
    "media_type",
    "parsed_entities_json",
    "analysis_result_json",
    "linked_objects_json",
}


class BootstrapMode(str, Enum):
    INITIALIZE_SCHEMA = "initialize_schema"
    STAMP_0001_AND_UPGRADE = "stamp_0001_and_upgrade"
    STAMP_HEAD = "stamp_head"
    UPGRADE = "upgrade"


@dataclass(frozen=True)
class SchemaState:
    tables: set[str]
    incoming_item_columns: set[str]
    has_alembic_version: bool


def migration_url(database_url: str) -> str:
    if "+aiosqlite" in database_url:
        return database_url.replace("+aiosqlite", "")
    if "+asyncpg" in database_url:
        return database_url.replace("+asyncpg", "+psycopg")
    return database_url


def classify_schema_state(state: SchemaState) -> BootstrapMode:
    if not state.tables:
        return BootstrapMode.INITIALIZE_SCHEMA
    if state.has_alembic_version:
        return BootstrapMode.UPGRADE
    if "incoming_items" not in state.tables:
        return BootstrapMode.UPGRADE
    if REQUIRED_AI_PIPELINE_COLUMNS - state.incoming_item_columns:
        return BootstrapMode.STAMP_0001_AND_UPGRADE
    return BootstrapMode.STAMP_HEAD


def _alembic_config() -> Config | None:
    root = Path(__file__).resolve().parent.parent
    alembic_ini = root / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic_ini_missing", path=str(alembic_ini))
        return None
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", migration_url(get_settings().database_url))
    return config


def inspect_schema_state(database_url: str) -> SchemaState:
    engine = create_engine(migration_url(database_url), poolclass=NullPool)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())
            incoming_item_columns: set[str] = set()
            if "incoming_items" in tables:
                incoming_item_columns = {column["name"] for column in inspector.get_columns("incoming_items")}
            return SchemaState(
                tables=tables,
                incoming_item_columns=incoming_item_columns,
                has_alembic_version="alembic_version" in tables,
            )
    finally:
        engine.dispose()


def _run_migration_plan(config: Config, mode: BootstrapMode) -> None:
    logger.info("database_bootstrap_mode", mode=mode.value)
    if mode == BootstrapMode.STAMP_0001_AND_UPGRADE:
        command.stamp(config, "0001_initial")
        command.upgrade(config, "head")
        logger.info("database_migrated", revision="head", from_revision="0001_initial")
        return
    if mode == BootstrapMode.STAMP_HEAD:
        command.stamp(config, "head")
        logger.info("database_stamped", revision="head")
        return
    command.upgrade(config, "head")
    logger.info("database_migrated", revision="head")


async def create_all(engine: AsyncEngine) -> None:
    config = _alembic_config()
    settings = get_settings()
    schema_state = inspect_schema_state(settings.database_url) if config is not None else SchemaState(set(), set(), False)
    mode = classify_schema_state(schema_state)

    if mode == BootstrapMode.INITIALIZE_SCHEMA:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if config is not None:
            command.stamp(config, "head")
            logger.info("database_initialized_and_stamped", revision="head")
        return

    if config is not None:
        try:
            _run_migration_plan(config, mode)
        except Exception:
            logger.exception("database_bootstrap_failed", mode=mode.value)
            raise

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)