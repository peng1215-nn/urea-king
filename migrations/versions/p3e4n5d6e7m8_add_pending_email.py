"""add pending_email: only verified accounts hold an email

Revision ID: p3e4n5d6e7m8
Revises: l2c3k4n5n6g7
Create Date: 2026-10-30 18:40:00.000000

变更内容：
- platform_users 加 pending_email（注册或更换后、尚未验证的邮箱，不唯一）。
- 现有未验证、未注销的账号：把 email 挪到 pending_email，email 置空。
  这样只有验证过的账号占用邮箱，别人用你的邮箱抢注也占不住。
"""

from alembic import op
import sqlalchemy as sa


revision = "p3e4n5d6e7m8"
down_revision = "l2c3k4n5n6g7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("platform_users", sa.Column("pending_email", sa.String(255), nullable=True))
    op.create_index("ix_platform_users_pending_email", "platform_users", ["pending_email"])
    op.execute(
        """
        UPDATE platform_users
        SET pending_email = email, email = NULL
        WHERE email_verified = 0
          AND deleted_at IS NULL
          AND email IS NOT NULL
        """
    )


def downgrade():
    # 未验证账号的邮箱挪回 email；若与已验证账号冲突则保持为空
    op.execute(
        """
        UPDATE platform_users AS u
        SET email = u.pending_email
        WHERE u.email IS NULL
          AND u.pending_email IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM platform_users v WHERE v.email = u.pending_email)
        """
    )
    op.drop_index("ix_platform_users_pending_email", table_name="platform_users")
    op.drop_column("platform_users", "pending_email")
