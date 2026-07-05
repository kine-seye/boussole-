"""add conversation states table

Revision ID: f3248ba9569d
Revises: 96184c2f96ae
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f3248ba9569d"
down_revision = "96184c2f96ae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("whatsapp_number", sa.String(20), unique=True, nullable=False),
        sa.Column("etape_courante", sa.String(50), server_default="debut"),
        sa.Column("reponses_temporaires", postgresql.JSON, server_default="{}"),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_conversation_states_whatsapp_number", "conversation_states", ["whatsapp_number"])


def downgrade() -> None:
    op.drop_table("conversation_states")
