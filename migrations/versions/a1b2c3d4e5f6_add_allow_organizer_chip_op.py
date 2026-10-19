"""add allow_organizer_chip_op to user_group_roles

Revision ID: a1b2c3d4e5f6
Revises: c2b9e03ea4aa
Create Date: 2026-10-19 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c2b9e03ea4aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'poker_user_group_roles',
        sa.Column('allow_organizer_chip_op', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('poker_user_group_roles', 'allow_organizer_chip_op')
