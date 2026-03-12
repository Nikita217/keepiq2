"""extend incoming items for ai pipeline

Revision ID: 0002_ai_pipeline
Revises: 0001_initial
Create Date: 2026-03-12 23:59:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_ai_pipeline"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incoming_items", sa.Column("original_chat_id", sa.BigInteger(), nullable=True))
    op.add_column("incoming_items", sa.Column("original_message_id", sa.Integer(), nullable=True))
    op.add_column("incoming_items", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.add_column("incoming_items", sa.Column("original_caption", sa.Text(), nullable=True))
    op.add_column("incoming_items", sa.Column("media_type", sa.String(length=64), nullable=True))
    op.add_column("incoming_items", sa.Column("parsed_entities_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("incoming_items", sa.Column("analysis_result_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("incoming_items", sa.Column("linked_objects_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.create_index("ix_incoming_items_original_chat_id", "incoming_items", ["original_chat_id"])
    op.create_index("ix_incoming_items_original_message_id", "incoming_items", ["original_message_id"])


def downgrade() -> None:
    op.drop_index("ix_incoming_items_original_message_id", table_name="incoming_items")
    op.drop_index("ix_incoming_items_original_chat_id", table_name="incoming_items")
    op.drop_column("incoming_items", "linked_objects_json")
    op.drop_column("incoming_items", "analysis_result_json")
    op.drop_column("incoming_items", "parsed_entities_json")
    op.drop_column("incoming_items", "media_type")
    op.drop_column("incoming_items", "original_caption")
    op.drop_column("incoming_items", "extracted_text")
    op.drop_column("incoming_items", "original_message_id")
    op.drop_column("incoming_items", "original_chat_id")
