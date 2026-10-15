"""remove invitation_code from users

Revision ID: f1a2b3c4d5e6
Revises: d4e5f6a7b8c9
Create Date: 2026-10-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'f1a2b3c4d5e6'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('users', 'invitation_code')


def downgrade():
    op.add_column('users', sa.Column('invitation_code', sa.String(100), nullable=True))
