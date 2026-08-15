"""add store_follows table

Revision ID: a1b2c3d4e5f6
Revises: d4e5f6a7b8c9
Create Date: 2026-08-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "store_follows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "user_id", name="uq_store_follows_store_user"),
    )
    op.create_index(op.f("ix_store_follows_id"), "store_follows", ["id"], unique=False)
    op.create_index(op.f("ix_store_follows_store_id"), "store_follows", ["store_id"], unique=False)
    op.create_index(op.f("ix_store_follows_user_id"), "store_follows", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_store_follows_user_id"), table_name="store_follows")
    op.drop_index(op.f("ix_store_follows_store_id"), table_name="store_follows")
    op.drop_index(op.f("ix_store_follows_id"), table_name="store_follows")
    op.drop_table("store_follows")
