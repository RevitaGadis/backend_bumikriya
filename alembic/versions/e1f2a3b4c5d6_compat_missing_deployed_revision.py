"""compat missing deployed revision

Revision ID: bcdeb2354033
Revises: b2c3d4e5f6a7
Create Date: 2026-08-13 21:35:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This revision was already stamped in production by a migration file that
    # is no longer present in the repository. Keep it as a no-op bridge so
    # Alembic can continue from that deployed database state.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
