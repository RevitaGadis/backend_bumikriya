"""add store profile columns

Revision ID: c9a7b3d5e8f1
Revises: f4e5d6c7b8a9
Create Date: 2026-08-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a7b3d5e8f1'
down_revision: Union[str, Sequence[str], None] = 'f4e5d6c7b8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('stores', sa.Column('tagline', sa.String(length=255), nullable=True))
    op.add_column('stores', sa.Column('banner', sa.String(length=255), nullable=True))
    op.add_column('stores', sa.Column('shipping_policy', sa.Text(), nullable=True))
    op.add_column('stores', sa.Column('return_policy', sa.Text(), nullable=True))
    op.add_column('stores', sa.Column('custom_policy', sa.Text(), nullable=True))
    op.add_column('stores', sa.Column('tags', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('stores', 'tags')
    op.drop_column('stores', 'custom_policy')
    op.drop_column('stores', 'return_policy')
    op.drop_column('stores', 'shipping_policy')
    op.drop_column('stores', 'banner')
    op.drop_column('stores', 'tagline')
