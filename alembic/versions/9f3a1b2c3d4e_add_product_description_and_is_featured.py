"""add product description and is_featured columns

Revision ID: 9f3a1b2c3d4e
Revises: 14a047d5f41a, a177e2fb3ecb
Create Date: 2026-08-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f3a1b2c3d4e'
down_revision: Union[str, Sequence[str], None] = ('14a047d5f41a', 'a177e2fb3ecb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('is_featured', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'is_featured')
    op.drop_column('products', 'description')