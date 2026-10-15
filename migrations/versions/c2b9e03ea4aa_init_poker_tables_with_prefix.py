"""init poker tables with prefix

Revision ID: c2b9e03ea4aa
Revises:
Create Date: 2026-10-15 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c2b9e03ea4aa'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('poker_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('invitation_code', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_users_id'), 'poker_users', ['id'], unique=False)
    op.create_index(op.f('ix_poker_users_username'), 'poker_users', ['username'], unique=True)

    op.create_table('poker_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_code', sa.String(length=50), nullable=False),
        sa.Column('group_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_groups_id'), 'poker_groups', ['id'], unique=False)
    op.create_index(op.f('ix_poker_groups_group_code'), 'poker_groups', ['group_code'], unique=True)

    op.create_table('poker_user_group_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['poker_groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['poker_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_user_group_roles_id'), 'poker_user_group_roles', ['id'], unique=False)

    op.create_table('poker_invitation_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('assigned_to', sa.String(length=100), nullable=True),
        sa.Column('group_code', sa.String(length=50), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False),
        sa.Column('is_used', sa.Integer(), nullable=False),
        sa.Column('used_by_username', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_invitation_codes_id'), 'poker_invitation_codes', ['id'], unique=False)
    op.create_index(op.f('ix_poker_invitation_codes_code'), 'poker_invitation_codes', ['code'], unique=True)

    op.create_table('poker_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=True),
        sa.Column('operator_username', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_audit_logs_id'), 'poker_audit_logs', ['id'], unique=False)

    op.create_table('poker_announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_announcements_id'), 'poker_announcements', ['id'], unique=False)

    op.create_table('poker_games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('organizer_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('total_buy_in', sa.Integer(), nullable=True),
        sa.Column('total_cash_out', sa.Integer(), nullable=True),
        sa.Column('is_balanced', sa.Integer(), nullable=True),
        sa.Column('player_count', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['poker_groups.id'], ),
        sa.ForeignKeyConstraint(['organizer_id'], ['poker_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_games_id'), 'poker_games', ['id'], unique=False)
    op.create_index(op.f('ix_poker_games_group_id'), 'poker_games', ['group_id'], unique=False)

    op.create_table('poker_game_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('total_buy_in', sa.Integer(), nullable=False),
        sa.Column('cash_out', sa.Integer(), nullable=True),
        sa.Column('net', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['poker_games.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['poker_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_game_players_id'), 'poker_game_players', ['id'], unique=False)
    op.create_index(op.f('ix_poker_game_players_game_id'), 'poker_game_players', ['game_id'], unique=False)

    op.create_table('poker_chip_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['poker_games.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['poker_users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['poker_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poker_chip_requests_id'), 'poker_chip_requests', ['id'], unique=False)
    op.create_index(op.f('ix_poker_chip_requests_game_id'), 'poker_chip_requests', ['game_id'], unique=False)


def downgrade() -> None:
    op.drop_table('poker_chip_requests')
    op.drop_table('poker_game_players')
    op.drop_table('poker_games')
    op.drop_table('poker_announcements')
    op.drop_table('poker_audit_logs')
    op.drop_table('poker_invitation_codes')
    op.drop_table('poker_user_group_roles')
    op.drop_table('poker_groups')
    op.drop_table('poker_users')
