"""add manager_only to poker_game_players

Revision ID: m5a6n7a8g9r0
Revises: r8a1u2d3i4t5
Create Date: 2026-10-31 10:10:00.000000

变更内容：
- poker_game_players 加 manager_only（默认 0）。
  局头可以只管理、不上桌；不上桌时也能买保险 / Anti，这时为他建一条 manager_only=1、
  is_active=0 的记录，用来记这些买入和结束时的结算。不占桌上名额，上桌后改回 0。
"""

from alembic import op
import sqlalchemy as sa


revision = "m5a6n7a8g9r0"
down_revision = "r8a1u2d3i4t5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "poker_game_players",
        sa.Column("manager_only", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("poker_game_players", "manager_only")
