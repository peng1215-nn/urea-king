"""add deleted_at to poker_users for post-deletion email cooldown

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-10-28 20:15:00.000000

变更内容：
- poker_users 加 deleted_at 字段（注销时间），用于限制同一邮箱注销后 24 小时内不能重新注册
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "poker_users",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("poker_users", "deleted_at")
