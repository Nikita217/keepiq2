"""add ai interpretation columns

Revision ID: 0003_ai_interpretation_v2
Revises: 0002_ai_pipeline
Create Date: 2026-03-13 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_ai_interpretation_v2"
down_revision = "0002_ai_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incoming_items", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("incoming_items", sa.Column("ai_primary_type", sa.String(length=32), nullable=True))
    op.add_column("incoming_items", sa.Column("ai_secondary_candidate_type", sa.String(length=32), nullable=True))
    op.add_column("incoming_items", sa.Column("ai_confidence", sa.Float(), nullable=True))
    op.create_index("ix_incoming_items_ai_primary_type", "incoming_items", ["ai_primary_type"])
    op.create_index("ix_incoming_items_ai_secondary_candidate_type", "incoming_items", ["ai_secondary_candidate_type"])


def downgrade() -> None:
    op.drop_index("ix_incoming_items_ai_secondary_candidate_type", table_name="incoming_items")
    op.drop_index("ix_incoming_items_ai_primary_type", table_name="incoming_items")
    op.drop_column("incoming_items", "ai_confidence")
    op.drop_column("incoming_items", "ai_secondary_candidate_type")
    op.drop_column("incoming_items", "ai_primary_type")
    op.drop_column("incoming_items", "ai_summary")
