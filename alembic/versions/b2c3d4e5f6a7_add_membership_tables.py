"""add membership tables

Revision ID: b2c3d4e5f6a7
Revises: a177e2fb3ecb
Create Date: 2026-08-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '9f3a1b2c3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists('membership_types'):
        op.create_table('membership_types',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('min_spending', sa.Float(), nullable=False),
            sa.Column('discount_percentage', sa.Float(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    if not _index_exists('membership_types', 'ix_membership_types_id'):
        op.create_index(op.f('ix_membership_types_id'), 'membership_types', ['id'], unique=False)
    if not _index_exists('membership_types', 'ix_membership_types_code'):
        op.create_index(op.f('ix_membership_types_code'), 'membership_types', ['code'], unique=True)

    if not _table_exists('user_memberships'):
        op.create_table('user_memberships',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('membership_type_id', sa.String(length=36), nullable=False),
            sa.Column('total_spending', sa.Float(), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['membership_type_id'], ['membership_types.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    if not _index_exists('user_memberships', 'ix_user_memberships_id'):
        op.create_index(op.f('ix_user_memberships_id'), 'user_memberships', ['id'], unique=False)
    if not _index_exists('user_memberships', 'ix_user_memberships_user_id'):
        op.create_index(op.f('ix_user_memberships_user_id'), 'user_memberships', ['user_id'], unique=True)
    if not _index_exists('user_memberships', 'ix_user_memberships_membership_type_id'):
        op.create_index(op.f('ix_user_memberships_membership_type_id'), 'user_memberships', ['membership_type_id'], unique=False)

    if not _table_exists('membership_benefits'):
        op.create_table('membership_benefits',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('membership_type_id', sa.String(length=36), nullable=False),
            sa.Column('benefit', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['membership_type_id'], ['membership_types.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    if not _index_exists('membership_benefits', 'ix_membership_benefits_id'):
        op.create_index(op.f('ix_membership_benefits_id'), 'membership_benefits', ['id'], unique=False)
    if not _index_exists('membership_benefits', 'ix_membership_benefits_membership_type_id'):
        op.create_index(op.f('ix_membership_benefits_membership_type_id'), 'membership_benefits', ['membership_type_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists('membership_benefits'):
        if _index_exists('membership_benefits', 'ix_membership_benefits_membership_type_id'):
            op.drop_index(op.f('ix_membership_benefits_membership_type_id'), table_name='membership_benefits')
        if _index_exists('membership_benefits', 'ix_membership_benefits_id'):
            op.drop_index(op.f('ix_membership_benefits_id'), table_name='membership_benefits')
        op.drop_table('membership_benefits')

    if _table_exists('user_memberships'):
        if _index_exists('user_memberships', 'ix_user_memberships_membership_type_id'):
            op.drop_index(op.f('ix_user_memberships_membership_type_id'), table_name='user_memberships')
        if _index_exists('user_memberships', 'ix_user_memberships_user_id'):
            op.drop_index(op.f('ix_user_memberships_user_id'), table_name='user_memberships')
        if _index_exists('user_memberships', 'ix_user_memberships_id'):
            op.drop_index(op.f('ix_user_memberships_id'), table_name='user_memberships')
        op.drop_table('user_memberships')

    if _table_exists('membership_types'):
        if _index_exists('membership_types', 'ix_membership_types_code'):
            op.drop_index(op.f('ix_membership_types_code'), table_name='membership_types')
        if _index_exists('membership_types', 'ix_membership_types_id'):
            op.drop_index(op.f('ix_membership_types_id'), table_name='membership_types')
        op.drop_table('membership_types')
