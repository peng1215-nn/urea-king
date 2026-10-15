"""Add missing columns to poker_invitation_codes.

The rename migration only added group_id; several columns present in the
model (assigned_to, role, used_by_user_id, used_by_username, used_at) did
not exist in the original table and need to be added.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns that exist in the model but were missing from the DB table.
    # Use ADD COLUMN IF NOT EXISTS to be safe in case a column already exists.
    op.execute("ALTER TABLE poker_invitation_codes ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(100)")
    op.execute("ALTER TABLE poker_invitation_codes ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'user'")
    op.execute("ALTER TABLE poker_invitation_codes ADD COLUMN IF NOT EXISTS used_by_user_id INTEGER")
    op.execute("ALTER TABLE poker_invitation_codes ADD COLUMN IF NOT EXISTS used_by_username VARCHAR(50)")
    op.execute("ALTER TABLE poker_invitation_codes ADD COLUMN IF NOT EXISTS used_at TIMESTAMP")


def downgrade() -> None:
    op.drop_column("poker_invitation_codes", "used_at")
    op.drop_column("poker_invitation_codes", "used_by_username")
    op.drop_column("poker_invitation_codes", "used_by_user_id")
    op.drop_column("poker_invitation_codes", "role")
    op.drop_column("poker_invitation_codes", "assigned_to")
