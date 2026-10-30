"""add poker_page_views table for login page visit tracking

Revision ID: p2v3i4e5w6s7
Revises: z9y8x7w6v5u4
Create Date: 2026-10-30 13:10:00.000000

变更内容：
- 新增 poker_page_views 表，记录登录页每日访问量
"""

from alembic import op
import sqlalchemy as sa


revision = "p2v3i4e5w6s7"
down_revision = "z9y8x7w6v5u4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "poker_page_views",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("date", sa.String(10), nullable=False, unique=True, index=True),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_table("poker_page_views")
