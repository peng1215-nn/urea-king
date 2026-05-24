"""add is_active to users

Revision ID: 315ae3471f6b
Revises: d7bbecd1c3aa
Create Date: 2026-05-24 15:14:13.127545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '315ae3471f6b'
down_revision: Union[str, Sequence[str], None] = 'd7bbecd1c3aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
