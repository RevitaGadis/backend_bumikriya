"""add payment midtrans

Revision ID: 14a047d5f41a
Revises: 064d1b4131c1
Create Date: 2026-08-13 07:42:05.063659

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '14a047d5f41a'
down_revision: Union[str, Sequence[str], None] = '064d1b4131c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration was generated while Transaction was missing from
    # alembic/env.py imports. The model still exists, so keep the table.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
