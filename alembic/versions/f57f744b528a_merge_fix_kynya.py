"""merge fix kynya

Revision ID: f57f744b528a
Revises: b8c9d1e2f3a4, e1f2a3b4c5d6
Create Date: 2026-08-15 21:43:17.547444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f57f744b528a'
down_revision: Union[str, Sequence[str], None] = ('b8c9d1e2f3a4', 'e1f2a3b4c5d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
