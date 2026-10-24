"""add indexes for game log and stats queries

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-24 11:30:00.000000

数据多了以后常用查询不再变慢：
- 牌局日志、统计：按组 + 状态筛选、按结束时间排序
- 组内成员：按组查
- 个人走势、是否在进行中的牌局里：按用户查
只加索引，不改任何数据。
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_games_group_status_ended", "poker_games", ["group_id", "status", "ended_at"])
    op.create_index("ix_user_group_roles_group_id", "poker_user_group_roles", ["group_id"])
    op.create_index("ix_game_players_user_id", "poker_game_players", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_game_players_user_id", table_name="poker_game_players")
    op.drop_index("ix_user_group_roles_group_id", table_name="poker_user_group_roles")
    op.drop_index("ix_games_group_status_ended", table_name="poker_games")
