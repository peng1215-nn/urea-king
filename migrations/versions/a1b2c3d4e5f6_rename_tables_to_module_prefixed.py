"""Rename tables to module-prefixed names for monorepo architecture.

Old → New:
  users              → platform_users
  groups             → poker_groups
  user_group_roles   → poker_user_group_roles
  invitation_codes   → poker_invitation_codes  (also: group_code str → group_id int FK)
  audit_logs         → poker_audit_logs
  announcements      → poker_announcements
  chip_requests      → poker_chip_requests

poker_games and poker_game_players already have correct names.

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Rename tables
    op.rename_table("users", "platform_users")
    op.rename_table("groups", "poker_groups")
    op.rename_table("user_group_roles", "poker_user_group_roles")
    op.rename_table("invitation_codes", "poker_invitation_codes")
    op.rename_table("audit_logs", "poker_audit_logs")
    op.rename_table("announcements", "poker_announcements")
    op.rename_table("chip_requests", "poker_chip_requests")

    # 2. invitation_codes: replace group_code (string) with group_id (integer FK)
    #    Add group_id column
    op.add_column(
        "poker_invitation_codes",
        sa.Column("group_id", sa.Integer(), nullable=True),
    )

    # Populate group_id by joining on group_code
    op.execute("""
        UPDATE poker_invitation_codes ic
        SET group_id = g.id
        FROM poker_groups g
        WHERE ic.group_code = g.group_code
    """)

    # Make group_id non-nullable
    op.alter_column("poker_invitation_codes", "group_id", nullable=False)

    # Add FK constraint from poker_invitation_codes.group_id → poker_groups.id
    op.create_foreign_key(
        "fk_poker_invitation_codes_group_id",
        "poker_invitation_codes",
        "poker_groups",
        ["group_id"],
        ["id"],
    )

    # Drop old group_code column (no longer needed)
    op.drop_column("poker_invitation_codes", "group_code")

    # 3. Drop cross-module FK constraints that reference old table names
    #    (poker_user_group_roles.group_id → poker_groups.id is an intra-poker FK, keep it)
    #    Old FK from user_group_roles.user_id → users.id was never a DB constraint
    #    (it was a logical reference), so nothing to drop there.
    #    Old FK from invitation_codes.group_code was a string match, also no DB FK.


def downgrade() -> None:
    # Restore group_code column
    op.add_column(
        "poker_invitation_codes",
        sa.Column("group_code", sa.String(length=20), nullable=True),
    )

    op.execute("""
        UPDATE poker_invitation_codes ic
        SET group_code = g.group_code
        FROM poker_groups g
        WHERE ic.group_id = g.id
    """)

    op.alter_column("poker_invitation_codes", "group_code", nullable=False)

    op.drop_constraint("fk_poker_invitation_codes_group_id", "poker_invitation_codes", type_="foreignkey")
    op.drop_column("poker_invitation_codes", "group_id")

    # Rename tables back
    op.rename_table("poker_chip_requests", "chip_requests")
    op.rename_table("poker_announcements", "announcements")
    op.rename_table("poker_audit_logs", "audit_logs")
    op.rename_table("poker_invitation_codes", "invitation_codes")
    op.rename_table("poker_user_group_roles", "user_group_roles")
    op.rename_table("poker_groups", "groups")
    op.rename_table("platform_users", "users")
