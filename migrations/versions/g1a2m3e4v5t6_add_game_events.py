"""add poker_game_events table for per-game audit reports

Revision ID: g1a2m3e4v5t6
Revises: p2v3i4e5w6s7
Create Date: 2026-10-30 16:10:00.000000

变更内容：
- 新增 poker_game_events 表：牌局里每次涉及人员或筹码的操作追加一行（只增不改），
  用于牌局日志里的"审计报告"。删除牌局时随之删除（外键 ON DELETE CASCADE）。
"""

from alembic import op
import sqlalchemy as sa


revision = "g1a2m3e4v5t6"
down_revision = "p2v3i4e5w6s7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "poker_game_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "game_id",
            sa.Integer(),
            sa.ForeignKey("poker_games.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_name", sa.String(50), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("target_name", sa.String(50), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=True),
        sa.Column("buy_type", sa.String(20), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_game_events_game_id_id", "poker_game_events", ["game_id", "id"])


def downgrade():
    op.drop_index("ix_game_events_game_id_id", table_name="poker_game_events")
    op.drop_table("poker_game_events")
