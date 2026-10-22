"""add invite_code_limit to poker_groups

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-10-22 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'poker_groups',
        sa.Column('invite_code_limit', sa.Integer(), nullable=False, server_default='27'),
    )


def downgrade() -> None:
    op.drop_column('poker_groups', 'invite_code_limit')
