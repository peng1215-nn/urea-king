"""add left_cash_out to poker_game_players

Revision ID: l1e2f3t4c5o6
Revises: g1a2m3e4v5t6
Create Date: 2026-10-30 17:00:00.000000

变更内容：
- poker_game_players 加 left_cash_out（中途结算离场时累计拿走的筹码，默认 0）。
  结束牌局时局头只填每人剩余的筹码，总卖出 = left_cash_out + 剩余筹码，由系统相加。
"""

from alembic import op
import sqlalchemy as sa


revision = "l1e2f3t4c5o6"
down_revision = "g1a2m3e4v5t6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "poker_game_players",
        sa.Column("left_cash_out", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("poker_game_players", "left_cash_out")
