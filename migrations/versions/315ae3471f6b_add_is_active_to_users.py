"""add is_active to users

Revision ID: 315ae3471f6b
Revises: d7bbecd1c3aa
Create Date: 2026-05-24 15:14:13.127545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '315ae3471f6b'
down_revision: Union[str, Sequence[str], None] = 'd7bbecd1c3aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "users",
        "is_active",
    )