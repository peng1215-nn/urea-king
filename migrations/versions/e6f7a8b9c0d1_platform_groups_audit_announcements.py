"""Add platform_groups, platform_user_group_roles, platform_announcements;
rename poker_audit_logs -> platform_audit_logs and add operator context fields.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create platform_groups
    op.create_table(
        "platform_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("group_code", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("group_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # 2. Create platform_user_group_roles
    op.create_table(
        "platform_user_group_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("group_id", sa.Integer(), nullable=False, index=True),
        sa.Column("role", sa.String(30), nullable=False, server_default="admin"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # 3. Rename poker_audit_logs -> platform_audit_logs
    op.execute("ALTER TABLE poker_audit_logs RENAME TO platform_audit_logs")

    # 4. Add new operator context fields to platform_audit_logs
    op.execute("ALTER TABLE platform_audit_logs ADD COLUMN IF NOT EXISTS operator_group_id INTEGER")
    op.execute("ALTER TABLE platform_audit_logs ADD COLUMN IF NOT EXISTS operator_group_code VARCHAR(50)")
    op.execute("ALTER TABLE platform_audit_logs ADD COLUMN IF NOT EXISTS operator_role VARCHAR(30)")

    # 5. Create platform_announcements
    op.create_table(
        "platform_announcements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_username", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("platform_announcements")
    op.execute("ALTER TABLE platform_audit_logs DROP COLUMN IF EXISTS operator_role")
    op.execute("ALTER TABLE platform_audit_logs DROP COLUMN IF EXISTS operator_group_code")
    op.execute("ALTER TABLE platform_audit_logs DROP COLUMN IF EXISTS operator_group_id")
    op.execute("ALTER TABLE platform_audit_logs RENAME TO poker_audit_logs")
    op.drop_table("platform_user_group_roles")
    op.drop_table("platform_groups")
