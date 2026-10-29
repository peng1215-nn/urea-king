"""backfill admin users into platform_user_modules

Revision ID: a2d3m4i5n6b7
Revises: m1o2d3u4l5e6
Create Date: 2026-10-29

管理员账号通过 bootstrap_admin 脚本创建，不走普通注册流程，
platform_user_modules 里没有记录。此迁移补录。
"""

from alembic import op

revision = "a2d3m4i5n6b7"
down_revision = "m1o2d3u4l5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 把所有 admin 角色用户补插一条 poker 模块记录（已有的跳过）
    op.execute("""
        INSERT INTO platform_user_modules (user_id, module, joined_at, is_active)
        SELECT DISTINCT ugr.user_id, 'poker', COALESCE(u.created_at, NOW()), 1
        FROM poker_user_group_roles ugr
        JOIN platform_users u ON u.id = ugr.user_id
        WHERE ugr.role = 'admin'
        ON CONFLICT (user_id, module) DO NOTHING
    """)


def downgrade() -> None:
    # 下线时只删管理员的模块记录（普通用户不动）
    op.execute("""
        DELETE FROM platform_user_modules
        WHERE user_id IN (
            SELECT user_id FROM poker_user_group_roles WHERE role = 'admin'
        )
        AND module = 'poker'
    """)
