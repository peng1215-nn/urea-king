"""add platform_user_modules table

Revision ID: m1o2d3u4l5e6
Revises: p1l2a3t4f5o6
Create Date: 2026-10-29

记录用户在哪些平台模块注册/登录过。
用户首次完成注册验证或首次登录某模块时自动插入一行。
"""

from alembic import op
import sqlalchemy as sa

revision = "m1o2d3u4l5e6"
down_revision = "p1l2a3t4f5o6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_user_modules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("platform_users.id"), nullable=False, index=True),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("user_id", "module", name="uq_user_modules_user_module"),
    )

    # 把现有 poker 用户全部补录一行（已验证邮箱的才算真正加入）
    op.execute("""
        INSERT INTO platform_user_modules (user_id, module, joined_at, is_active)
        SELECT id, 'poker', COALESCE(created_at, NOW()), 1
        FROM platform_users
        WHERE email_verified = 1
    """)


def downgrade() -> None:
    op.drop_table("platform_user_modules")
