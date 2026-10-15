"""platform group registry: add module/created_by_admin_id to platform_groups,
add platform_group_id to poker_groups, add created_by to poker_invitation_codes

Revision ID: a2b3c4d5e6f7
Revises: f0a1b2c3d4e5
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'f0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # platform_groups: add module and created_by_admin_id
    op.add_column('platform_groups',
        sa.Column('module', sa.String(length=30), nullable=True))
    op.add_column('platform_groups',
        sa.Column('created_by_admin_id', sa.Integer(), nullable=True))
    op.create_index('ix_platform_groups_module', 'platform_groups', ['module'])

    # poker_groups: add platform_group_id
    op.add_column('poker_groups',
        sa.Column('platform_group_id', sa.Integer(), nullable=True))
    op.create_index('ix_poker_groups_platform_group_id', 'poker_groups', ['platform_group_id'])

    # poker_invitation_codes: add created_by (default "organizer")
    op.add_column('poker_invitation_codes',
        sa.Column('created_by', sa.String(length=20), nullable=False,
                  server_default='organizer'))


def downgrade() -> None:
    op.drop_column('poker_invitation_codes', 'created_by')
    op.drop_index('ix_poker_groups_platform_group_id', table_name='poker_groups')
    op.drop_column('poker_groups', 'platform_group_id')
    op.drop_index('ix_platform_groups_module', table_name='platform_groups')
    op.drop_column('platform_groups', 'created_by_admin_id')
    op.drop_column('platform_groups', 'module')
