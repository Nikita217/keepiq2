"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-12 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("telegram_user_id"),
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"])

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("auto_create_high_confidence", sa.Boolean(), nullable=False),
        sa.Column("default_reminder_lead_hours", sa.Integer(), nullable=False),
        sa.Column("enable_ai_reply_drafts", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"])

    op.create_table(
        "daily_digest_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("morning_enabled", sa.Boolean(), nullable=False),
        sa.Column("morning_time", sa.String(length=5), nullable=False),
        sa.Column("evening_enabled", sa.Boolean(), nullable=False),
        sa.Column("evening_time", sa.String(length=5), nullable=False),
        sa.Column("include_overdue", sa.Boolean(), nullable=False),
        sa.Column("include_inbox", sa.Boolean(), nullable=False),
        sa.Column("include_events", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_daily_digest_settings_user_id", "daily_digest_settings", ["user_id"])

    op.create_table(
        "incoming_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_message_id", sa.Integer(), nullable=True),
        sa.Column("telegram_update_id", sa.Integer(), nullable=True),
        sa.Column("incoming_type", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("proposed_type", sa.String(length=32), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("needs_confirmation", sa.Boolean(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_incoming_items_user_id": ["user_id"],
        "ix_incoming_items_telegram_chat_id": ["telegram_chat_id"],
        "ix_incoming_items_telegram_message_id": ["telegram_message_id"],
        "ix_incoming_items_telegram_update_id": ["telegram_update_id"],
        "ix_incoming_items_incoming_type": ["incoming_type"],
        "ix_incoming_items_parse_status": ["parse_status"],
    }.items():
        op.create_index(index_name, "incoming_items", columns)

    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=True),
        sa.Column("telegram_unique_file_id", sa.String(length=255), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_attachments_incoming_item_id", "attachments", ["incoming_item_id"])
    op.create_index("ix_attachments_content_type", "attachments", ["content_type"])

    op.create_table(
        "parsed_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_parsed_entities_incoming_item_id", "parsed_entities", ["incoming_item_id"])
    op.create_index("ix_parsed_entities_entity_type", "parsed_entities", ["entity_type"])

    op.create_table(
        "ai_analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("proposed_type", sa.String(length=32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("fallback_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_analysis_results_incoming_item_id", "ai_analysis_results", ["incoming_item_id"])

    op.create_table(
        "object_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_type", sa.String(length=32), nullable=False),
        sa.Column("object_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_object_links_incoming_item_id", "object_links", ["incoming_item_id"])
    op.create_index("ix_object_links_object_type", "object_links", ["object_type"])
    op.create_index("ix_object_links_object_id", "object_links", ["object_id"])

    op.create_table(
        "processing_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="CASCADE"), nullable=True),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_processing_logs_incoming_item_id", "processing_logs", ["incoming_item_id"])
    op.create_index("ix_processing_logs_stage", "processing_logs", ["stage"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("category_hint", sa.String(length=64), nullable=True),
        sa.Column("extra_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_tasks_user_id": ["user_id"],
        "ix_tasks_source_incoming_item_id": ["source_incoming_item_id"],
        "ix_tasks_status": ["status"],
        "ix_tasks_due_at": ["due_at"],
        "ix_tasks_scheduled_for": ["scheduled_for"],
    }.items():
        op.create_index(index_name, "tasks", columns)

    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("place_name", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("booking_reference", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("extra_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_events_user_id": ["user_id"],
        "ix_events_source_incoming_item_id": ["source_incoming_item_id"],
        "ix_events_starts_at": ["starts_at"],
        "ix_events_status": ["status"],
    }.items():
        op.create_index(index_name, "events", columns)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_id", sa.Uuid(), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remind_on", sa.Date(), nullable=True),
        sa.Column("recurrence_rule", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_reminders_user_id": ["user_id"],
        "ix_reminders_source_incoming_item_id": ["source_incoming_item_id"],
        "ix_reminders_task_id": ["task_id"],
        "ix_reminders_event_id": ["event_id"],
        "ix_reminders_remind_at": ["remind_at"],
        "ix_reminders_remind_on": ["remind_on"],
        "ix_reminders_status": ["status"],
    }.items():
        op.create_index(index_name, "reminders", columns)

    op.create_table(
        "notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("extra_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_notes_user_id": ["user_id"],
        "ix_notes_source_incoming_item_id": ["source_incoming_item_id"],
        "ix_notes_kind": ["kind"],
    }.items():
        op.create_index(index_name, "notes", columns)

    op.create_table(
        "lists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("extra_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_lists_user_id": ["user_id"],
        "ix_lists_source_incoming_item_id": ["source_incoming_item_id"],
        "ix_lists_kind": ["kind"],
    }.items():
        op.create_index(index_name, "lists", columns)

    op.create_table(
        "list_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("list_id", sa.Uuid(), sa.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_list_items_list_id", "list_items", ["list_id"])

    op.create_table(
        "reply_later_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("conversation_summary", sa.Text(), nullable=True),
        sa.Column("suggested_replies_json", sa.JSON(), nullable=False),
        sa.Column("reply_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for index_name, columns in {
        "ix_reply_later_items_user_id": ["user_id"],
        "ix_reply_later_items_source_incoming_item_id": ["source_incoming_item_id"],
        "ix_reply_later_items_reply_due_at": ["reply_due_at"],
        "ix_reply_later_items_status": ["status"],
    }.items():
        op.create_index(index_name, "reply_later_items", columns)

    op.create_table(
        "saved_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_incoming_item_id", sa.Uuid(), sa.ForeignKey("incoming_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("extra_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_saved_items_user_id", "saved_items", ["user_id"])
    op.create_index("ix_saved_items_source_incoming_item_id", "saved_items", ["source_incoming_item_id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("color", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "slug"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "slug"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])


def downgrade() -> None:
    for table in [
        "tags",
        "categories",
        "saved_items",
        "reply_later_items",
        "list_items",
        "lists",
        "notes",
        "reminders",
        "events",
        "tasks",
        "processing_logs",
        "object_links",
        "ai_analysis_results",
        "parsed_entities",
        "attachments",
        "incoming_items",
        "daily_digest_settings",
        "user_settings",
        "users",
    ]:
        op.drop_table(table)
