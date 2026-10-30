"""add non-negative check on poker_game_players.left_cash_out

Revision ID: l2c3k4n5n6g7
Revises: l1e2f3t4c5o6
Create Date: 2026-10-30 17:40:00.000000

变更内容：
- poker_game_players.left_cash_out 加 CHECK (>= 0)，和 cash_out 一致。
"""

from alembic import op


revision = "l2c3k4n5n6g7"
down_revision = "l1e2f3t4c5o6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "ck_game_players_left_cash_out_nonneg",
        "poker_game_players",
        "left_cash_out >= 0",
    )


def downgrade():
    op.drop_constraint("ck_game_players_left_cash_out_nonneg", "poker_game_players", type_="check")
