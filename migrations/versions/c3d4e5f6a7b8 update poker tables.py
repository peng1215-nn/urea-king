"""update poker tables remove insurance anti fields add chip request type

Revision ID: c3d4e5f6a7b8
Revises: 70bc1ce12bfe
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = '70bc1ce12bfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('poker_game_players', 'insurance_paid')
    op.drop_column('poker_game_players', 'insurance_received')
    op.drop_column('poker_game_players', 'anti_received')

    op.drop_column('poker_games', 'insurance_collected')
    op.drop_column('poker_games', 'insurance_paid_out')
    op.drop_column('poker_games', 'anti_paid_out')
    op.drop_column('poker_games', 'organizer_net')

    op.add_column(
        'chip_requests',
        sa.Column(
            'type',
            sa.String(length=20),
            nullable=False,
            server_default='normal',
        )
    )


def downgrade() -> None:
    op.drop_column('chip_requests', 'type')

    op.add_column('poker_games', sa.Column('organizer_net', sa.Integer(), nullable=True))
    op.add_column('poker_games', sa.Column('anti_paid_out', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('poker_games', sa.Column('insurance_paid_out', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('poker_games', sa.Column('insurance_collected', sa.Integer(), nullable=False, server_default='0'))

    op.add_column('poker_game_players', sa.Column('anti_received', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('poker_game_players', sa.Column('insurance_received', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('poker_game_players', sa.Column('insurance_paid', sa.Integer(), nullable=False, server_default='0'))