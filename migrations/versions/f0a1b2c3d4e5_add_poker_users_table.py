"""add poker_users table

Revision ID: f0a1b2c3d4e5
Revises: e6f7a8b9c0d1, d4e5f6a7b8c9
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = ('e6f7a8b9c0d1', 'd4e5f6a7b8c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'poker_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_poker_users_id', 'poker_users', ['id'], unique=False)
    op.create_index('ix_poker_users_username', 'poker_users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_poker_users_username', table_name='poker_users')
    op.drop_index('ix_poker_users_id', table_name='poker_users')
    op.drop_table('poker_users')
