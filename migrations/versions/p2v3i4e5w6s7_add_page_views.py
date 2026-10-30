"""add poker_site_counters table for site-wide daily stats

Revision ID: p2v3i4e5w6s7
Revises: z9y8x7w6v5u4
Create Date: 2026-10-30 13:10:00.000000

变更内容：
- 新增 poker_site_counters 表，按 key+date 记录每日统计量
  key: 'login_page_view'（登录页 PV）| 'login_success'（登录成功次数）
"""

from alembic import op
import sqlalchemy as sa


revision = "p2v3i4e5w6s7"
down_revision = "z9y8x7w6v5u4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "poker_site_counters",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("key", sa.String(50), nullable=False, index=True),
        sa.Column("date", sa.String(10), nullable=False, index=True),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("key", "date", name="uq_site_counter_key_date"),
    )


def downgrade():
    op.drop_table("poker_site_counters")
