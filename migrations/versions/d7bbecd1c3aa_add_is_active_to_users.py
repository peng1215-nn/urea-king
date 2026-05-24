"""add is_active to users

Revision ID: d7bbecd1c3aa
Revises: 0b12cf532515
Create Date: 2026-05-24 15:08:39.658729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7bbecd1c3aa'
down_revision: Union[str, Sequence[str], None] = '0b12cf532515'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
