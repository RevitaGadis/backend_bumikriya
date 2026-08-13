"""merge migration heads

Revision ID: bcdeb2354033
Revises: 14a047d5f41a, a177e2fb3ecb
Create Date: 2026-08-13 08:50:56.266100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcdeb2354033'
down_revision: Union[str, Sequence[str], None] = ('14a047d5f41a', 'a177e2fb3ecb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
