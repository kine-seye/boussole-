"""add faq entries table

Revision ID: cf393028adb2
Revises: afb1c953d4ed
Create Date: 2026-07-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "cf393028adb2"
down_revision = "afb1c953d4ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "faq_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pays", sa.String(100), nullable=False),
        sa.Column("type_demarche", sa.String(100), nullable=True),
        sa.Column("sujet", sa.String(255), nullable=False),
        sa.Column("question_type", sa.String(255), nullable=False),
        sa.Column("reponse", sa.Text, nullable=False),
        sa.Column("source_officielle", sa.String(500), nullable=False),
        sa.Column("date_verification", sa.String(20), nullable=False),
    )
    op.create_index("ix_faq_entries_pays", "faq_entries", ["pays"])


def downgrade() -> None:
    op.drop_table("faq_entries")
