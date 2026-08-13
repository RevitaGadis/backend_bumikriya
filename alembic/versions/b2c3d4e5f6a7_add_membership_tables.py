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
down_revision: Union[str, Sequence[str], None] = 'a177e2fb3ecb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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
    op.create_index(op.f('ix_membership_types_id'), 'membership_types', ['id'], unique=False)
    op.create_index(op.f('ix_membership_types_code'), 'membership_types', ['code'], unique=True)

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
    op.create_index(op.f('ix_user_memberships_id'), 'user_memberships', ['id'], unique=False)
    op.create_index(op.f('ix_user_memberships_user_id'), 'user_memberships', ['user_id'], unique=True)
    op.create_index(op.f('ix_user_memberships_membership_type_id'), 'user_memberships', ['membership_type_id'], unique=False)

    op.create_table('membership_benefits',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('membership_type_id', sa.String(length=36), nullable=False),
        sa.Column('benefit', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['membership_type_id'], ['membership_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_membership_benefits_id'), 'membership_benefits', ['id'], unique=False)
    op.create_index(op.f('ix_membership_benefits_membership_type_id'), 'membership_benefits', ['membership_type_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_membership_benefits_membership_type_id'), table_name='membership_benefits')
    op.drop_index(op.f('ix_membership_benefits_id'), table_name='membership_benefits')
    op.drop_table('membership_benefits')

    op.drop_index(op.f('ix_user_memberships_membership_type_id'), table_name='user_memberships')
    op.drop_index(op.f('ix_user_memberships_user_id'), table_name='user_memberships')
    op.drop_index(op.f('ix_user_memberships_id'), table_name='user_memberships')
    op.drop_table('user_memberships')

    op.drop_index(op.f('ix_membership_types_code'), table_name='membership_types')
    op.drop_index(op.f('ix_membership_types_id'), table_name='membership_types')
    op.drop_table('membership_types')
