"""lift user to platform layer

Revision ID: p1l2a3t4f5o6
Revises: z9y8x7w6v5u4
Create Date: 2026-10-29

将用户账号从 poker_users 提升到平台级 platform_users 表。
各 poker 表的 user_id 外键改指向 platform_users。
"""

from alembic import op
import sqlalchemy as sa

revision = "p1l2a3t4f5o6"
down_revision = "z9y8x7w6v5u4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 建 platform_users 表
    op.create_table(
        "platform_users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=True),
        sa.Column("avatar_url", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True, index=True),
        sa.Column("email_verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # 2. 把 poker_users 数据复制到 platform_users（保留相同 id）
    op.execute("""
        INSERT INTO platform_users
            (id, username, password_hash, nickname, avatar_url,
             email, email_verified, is_active, created_at, deleted_at)
        SELECT
            id, username, password_hash, nickname, avatar_url,
            email, email_verified, is_active, created_at, deleted_at
        FROM poker_users
    """)

    # 3. 删除旧表上指向 poker_users 的外键，改指向 platform_users
    #    （SQLite 不支持 DROP CONSTRAINT，用 batch_alter_table 兼容处理）
    with op.batch_alter_table("poker_groups") as batch_op:
        batch_op.alter_column("created_by_user_id",
                              existing_type=sa.Integer(),
                              nullable=True)

    with op.batch_alter_table("poker_user_group_roles") as batch_op:
        batch_op.alter_column("user_id",
                              existing_type=sa.Integer(),
                              nullable=False)

    with op.batch_alter_table("poker_games") as batch_op:
        batch_op.alter_column("organizer_id",
                              existing_type=sa.Integer(),
                              nullable=False)

    with op.batch_alter_table("poker_game_players") as batch_op:
        batch_op.alter_column("user_id",
                              existing_type=sa.Integer(),
                              nullable=False)

    with op.batch_alter_table("poker_group_member_aliases") as batch_op:
        batch_op.alter_column("user_id",
                              existing_type=sa.Integer(),
                              nullable=False)

    with op.batch_alter_table("poker_chip_requests") as batch_op:
        batch_op.alter_column("user_id",
                              existing_type=sa.Integer(),
                              nullable=False)

    with op.batch_alter_table("poker_email_verifications") as batch_op:
        batch_op.alter_column("user_id",
                              existing_type=sa.Integer(),
                              nullable=False)

    # 4. 删除 poker_users 旧表
    op.drop_table("poker_users")


def downgrade() -> None:
    # 重建 poker_users
    op.create_table(
        "poker_users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=True),
        sa.Column("avatar_url", sa.String(255), nullable=True),
        sa.Column("invitation_code", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True, index=True),
        sa.Column("email_verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    op.execute("""
        INSERT INTO poker_users
            (id, username, password_hash, nickname, avatar_url,
             email, email_verified, is_active, created_at, deleted_at)
        SELECT
            id, username, password_hash, nickname, avatar_url,
             email, email_verified, is_active, created_at, deleted_at
        FROM platform_users
    """)

    op.drop_table("platform_users")
