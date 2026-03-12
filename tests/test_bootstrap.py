from db.bootstrap import BootstrapMode, REQUIRED_AI_PIPELINE_COLUMNS, SchemaState, classify_schema_state, migration_url


def test_migration_url_uses_psycopg_for_asyncpg() -> None:
    assert migration_url("postgresql+asyncpg://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_classify_schema_state_for_empty_database() -> None:
    state = SchemaState(tables=set(), incoming_item_columns=set(), has_alembic_version=False)

    assert classify_schema_state(state) == BootstrapMode.INITIALIZE_SCHEMA


def test_classify_schema_state_for_legacy_database_without_pipeline_columns() -> None:
    state = SchemaState(
        tables={"users", "incoming_items", "tasks"},
        incoming_item_columns={"id", "user_id", "raw_text"},
        has_alembic_version=False,
    )

    assert classify_schema_state(state) == BootstrapMode.STAMP_0001_AND_UPGRADE


def test_classify_schema_state_for_current_database_without_alembic_version() -> None:
    state = SchemaState(
        tables={"users", "incoming_items", "tasks"},
        incoming_item_columns={"id", "user_id", "raw_text", *REQUIRED_AI_PIPELINE_COLUMNS},
        has_alembic_version=False,
    )

    assert classify_schema_state(state) == BootstrapMode.STAMP_HEAD


def test_classify_schema_state_for_managed_database() -> None:
    state = SchemaState(
        tables={"users", "incoming_items", "alembic_version"},
        incoming_item_columns={"id", "user_id"},
        has_alembic_version=True,
    )

    assert classify_schema_state(state) == BootstrapMode.UPGRADE