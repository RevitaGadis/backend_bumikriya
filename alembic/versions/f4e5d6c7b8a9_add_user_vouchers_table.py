"""add user_vouchers table

Revision ID: f4e5d6c7b8a9
Revises: a3b5c7d9e1f3
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4e5d6c7b8a9"
down_revision: Union[str, Sequence[str], None] = "a3b5c7d9e1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("user_vouchers"):
        op.create_table(
            "user_vouchers",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("voucher_id", sa.String(length=36), nullable=False),
            sa.Column("level_code", sa.String(length=50), nullable=True),
            sa.Column("is_claimed", sa.Boolean(), nullable=False),
            sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["voucher_id"], ["vouchers.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("user_vouchers", "ix_user_vouchers_id"):
        op.create_index(op.f("ix_user_vouchers_id"), "user_vouchers", ["id"], unique=False)
    if not _index_exists("user_vouchers", "ix_user_vouchers_user_id"):
        op.create_index(op.f("ix_user_vouchers_user_id"), "user_vouchers", ["user_id"], unique=False)
    if not _index_exists("user_vouchers", "ix_user_vouchers_voucher_id"):
        op.create_index(op.f("ix_user_vouchers_voucher_id"), "user_vouchers", ["voucher_id"], unique=False)
    if not _index_exists("user_vouchers", "ix_user_vouchers_level_code"):
        op.create_index(op.f("ix_user_vouchers_level_code"), "user_vouchers", ["level_code"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists("user_vouchers"):
        if _index_exists("user_vouchers", "ix_user_vouchers_level_code"):
            op.drop_index(op.f("ix_user_vouchers_level_code"), table_name="user_vouchers")
        if _index_exists("user_vouchers", "ix_user_vouchers_voucher_id"):
            op.drop_index(op.f("ix_user_vouchers_voucher_id"), table_name="user_vouchers")
        if _index_exists("user_vouchers", "ix_user_vouchers_user_id"):
            op.drop_index(op.f("ix_user_vouchers_user_id"), table_name="user_vouchers")
        if _index_exists("user_vouchers", "ix_user_vouchers_id"):
            op.drop_index(op.f("ix_user_vouchers_id"), table_name="user_vouchers")
        op.drop_table("user_vouchers")
