"""audit-log indexes, 64-bit ledger totals, unique nickname

Revision ID: r8a1u2d3i4t5
Revises: p3e4n5d6e7m8
Create Date: 2026-10-30 19:10:00.000000

变更内容：
- poker_audit_logs 加索引（created_at；action + created_at），系统日志页翻页、筛选不再扫全表。
- 牌局金额累计列改为 BIGINT（poker_games.total_buy_in / total_cash_out；
  poker_game_players.total_buy_in / cash_out / net / left_cash_out），避免超过 32 位整数上限。
- 昵称唯一（不区分大小写，已注销的账号不算）：lower(nickname) 上的部分唯一索引。
"""

from alembic import op
import sqlalchemy as sa


revision = "r8a1u2d3i4t5"
down_revision = "p3e4n5d6e7m8"
branch_labels = None
depends_on = None


BIGINT_COLUMNS = [
    ("poker_games", "total_buy_in"),
    ("poker_games", "total_cash_out"),
    ("poker_game_players", "total_buy_in"),
    ("poker_game_players", "cash_out"),
    ("poker_game_players", "net"),
    ("poker_game_players", "left_cash_out"),
]


def upgrade():
    op.create_index("ix_audit_logs_created_at", "poker_audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_action_created_at", "poker_audit_logs", ["action", "created_at"])

    for table, column in BIGINT_COLUMNS:
        op.alter_column(table, column, type_=sa.BigInteger(), existing_type=sa.Integer())

    op.execute(
        "CREATE UNIQUE INDEX uq_platform_users_nickname_lower "
        "ON platform_users (lower(nickname)) WHERE deleted_at IS NULL"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_platform_users_nickname_lower")
    for table, column in BIGINT_COLUMNS:
        op.alter_column(table, column, type_=sa.Integer(), existing_type=sa.BigInteger())
    op.drop_index("ix_audit_logs_action_created_at", table_name="poker_audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="poker_audit_logs")
