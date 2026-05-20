"""merge migration heads

Revision ID: dabe5ba28b43
Revises: 523d8aabcc83, 8a0acdb37e54
Create Date: 2026-05-20 16:50:50.762973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dabe5ba28b43'
down_revision: Union[str, Sequence[str], None] = ('523d8aabcc83', '8a0acdb37e54')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
