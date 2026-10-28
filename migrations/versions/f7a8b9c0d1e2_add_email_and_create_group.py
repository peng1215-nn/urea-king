"""add email verification and group creation support

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-10-28 12:00:00.000000

变更内容：
- poker_users 加 email（唯一）、email_verified 字段
- 新增 poker_email_verifications 表（注册验证 + 找回密码共用）
- poker_groups 加 created_by_user_id 字段（记录哪个用户创建了这个组）
"""

from alembic import op
import sqlalchemy as sa


revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade():
    # ── poker_users：加 email 和 email_verified ──
    op.add_column(
        "poker_users",
        sa.Column("email", sa.String(255), nullable=True),
    )
    op.add_column(
        "poker_users",
        sa.Column("email_verified", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_poker_users_email",
        "poker_users",
        ["email"],
        unique=True,
    )

    # ── poker_groups：加 created_by_user_id ──
    op.add_column(
        "poker_groups",
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("poker_users.id"),
            nullable=True,
        ),
    )

    # ── poker_email_verifications：注册验证和找回密码共用 ──
    op.create_table(
        "poker_email_verifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("poker_users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("token", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column(
            "purpose",
            sa.String(30),
            nullable=False,
        ),  # 'verify_email' | 'reset_password'
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_table("poker_email_verifications")
    op.drop_index("ix_poker_users_email", table_name="poker_users")
    op.drop_column("poker_users", "email_verified")
    op.drop_column("poker_users", "email")
    op.drop_column("poker_groups", "created_by_user_id")
