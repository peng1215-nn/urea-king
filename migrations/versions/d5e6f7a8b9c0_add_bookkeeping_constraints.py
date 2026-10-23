"""add bookkeeping integrity constraints

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-10-23 22:00:00.000000

防重复与金额规则，作为代码检查之外的最后一道保护：
- 同一组同一人只能有一条成员记录
- 同一局同一人只能有一条玩家记录
- 同一组同一人只能有一个备注名
- 买入、带走金额不能为负；申请金额必须大于 0
- 牌局状态只能是 ongoing / finished

升级前先检查现有数据。只要有一条不符合，就停止升级并列出问题记录，
不会自动删除或修改任何数据（整个升级在一个事务里，失败时什么都不会改）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (说明, 查找违规记录的 SQL)
PRECHECKS = [
    (
        "同一组里同一个人有多条成员记录 (poker_user_group_roles)",
        """
        SELECT user_id, group_id, COUNT(*) AS n
        FROM poker_user_group_roles
        GROUP BY user_id, group_id HAVING COUNT(*) > 1
        """,
    ),
    (
        "同一局里同一个人有多条玩家记录 (poker_game_players)",
        """
        SELECT game_id, user_id, COUNT(*) AS n
        FROM poker_game_players
        GROUP BY game_id, user_id HAVING COUNT(*) > 1
        """,
    ),
    (
        "同一组里同一个人有多个备注名 (poker_group_member_aliases)",
        """
        SELECT group_id, user_id, COUNT(*) AS n
        FROM poker_group_member_aliases
        GROUP BY group_id, user_id HAVING COUNT(*) > 1
        """,
    ),
    (
        "玩家买入或带走金额为负数 (poker_game_players)",
        """
        SELECT id, game_id, user_id, total_buy_in, cash_out
        FROM poker_game_players
        WHERE total_buy_in < 0 OR cash_out < 0
        """,
    ),
    (
        "申请金额不大于 0 (poker_chip_requests)",
        """
        SELECT id, game_id, user_id, amount
        FROM poker_chip_requests
        WHERE amount <= 0
        """,
    ),
    (
        "牌局状态不是 ongoing / finished (poker_games)",
        """
        SELECT id, group_id, status
        FROM poker_games
        WHERE status NOT IN ('ongoing', 'finished')
        """,
    ),
]


def _check_existing_data():
    bind = op.get_bind()
    problems = []

    for title, sql in PRECHECKS:
        rows = bind.execute(sa.text(sql)).fetchall()
        if rows:
            sample = "\n".join(f"    {tuple(row)}" for row in rows[:20])
            more = f"\n    ... 共 {len(rows)} 条" if len(rows) > 20 else ""
            problems.append(f"- {title}:\n{sample}{more}")

    if problems:
        raise RuntimeError(
            "现有数据不符合新规则，升级已停止，没有修改任何数据。"
            "请先处理以下记录后再部署：\n" + "\n".join(problems)
        )


def upgrade() -> None:
    _check_existing_data()

    op.create_unique_constraint(
        "uq_user_group_roles_user_group", "poker_user_group_roles", ["user_id", "group_id"]
    )
    op.create_unique_constraint(
        "uq_game_players_game_user", "poker_game_players", ["game_id", "user_id"]
    )
    op.create_unique_constraint(
        "uq_member_aliases_group_user", "poker_group_member_aliases", ["group_id", "user_id"]
    )

    op.create_check_constraint(
        "ck_game_players_buy_in_nonneg", "poker_game_players", "total_buy_in >= 0"
    )
    op.create_check_constraint(
        "ck_game_players_cash_out_nonneg", "poker_game_players", "cash_out IS NULL OR cash_out >= 0"
    )
    op.create_check_constraint(
        "ck_chip_requests_amount_pos", "poker_chip_requests", "amount > 0"
    )
    op.create_check_constraint(
        "ck_games_status", "poker_games", "status IN ('ongoing', 'finished')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_games_status", "poker_games", type_="check")
    op.drop_constraint("ck_chip_requests_amount_pos", "poker_chip_requests", type_="check")
    op.drop_constraint("ck_game_players_cash_out_nonneg", "poker_game_players", type_="check")
    op.drop_constraint("ck_game_players_buy_in_nonneg", "poker_game_players", type_="check")
    op.drop_constraint("uq_member_aliases_group_user", "poker_group_member_aliases", type_="unique")
    op.drop_constraint("uq_game_players_game_user", "poker_game_players", type_="unique")
    op.drop_constraint("uq_user_group_roles_user_group", "poker_user_group_roles", type_="unique")
