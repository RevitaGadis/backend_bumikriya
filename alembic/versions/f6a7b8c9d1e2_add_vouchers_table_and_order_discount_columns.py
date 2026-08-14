"""add vouchers table and order discount columns

Revision ID: f6a7b8c9d1e2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d1e2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _column_exists(table_name: str, column_name: str) -> bool:
    columns = [col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("vouchers"):
        op.create_table(
            "vouchers",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("discount_percent", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("max_discount", sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column("min_purchase", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("quota", sa.Integer(), nullable=False),
            sa.Column("used_count", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("vouchers", "ix_vouchers_id"):
        op.create_index(op.f("ix_vouchers_id"), "vouchers", ["id"], unique=False)
    if not _index_exists("vouchers", "ix_vouchers_code"):
        op.create_index(op.f("ix_vouchers_code"), "vouchers", ["code"], unique=True)

    if not _column_exists("orders", "discount"):
        op.add_column(
            "orders",
            sa.Column("discount", sa.Numeric(precision=12, scale=2), server_default=sa.text("0.00"), nullable=False),
        )

    if not _column_exists("orders", "voucher_id"):
        op.add_column(
            "orders",
            sa.Column("voucher_id", sa.String(length=36), nullable=True),
        )
        op.create_foreign_key(
            "fk_orders_voucher_id",
            "orders",
            "vouchers",
            ["voucher_id"],
            ["id"],
        )
    if not _index_exists("orders", "ix_orders_voucher_id"):
        op.create_index(op.f("ix_orders_voucher_id"), "orders", ["voucher_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists("orders"):
        if _index_exists("orders", "ix_orders_voucher_id"):
            op.drop_index(op.f("ix_orders_voucher_id"), table_name="orders")
        if _column_exists("orders", "voucher_id"):
            try:
                op.drop_constraint("fk_orders_voucher_id", "orders", type_="foreignkey")
            except Exception:
                pass
            op.drop_column("orders", "voucher_id")
        if _column_exists("orders", "discount"):
            op.drop_column("orders", "discount")

    if _table_exists("vouchers"):
        if _index_exists("vouchers", "ix_vouchers_code"):
            op.drop_index(op.f("ix_vouchers_code"), table_name="vouchers")
        if _index_exists("vouchers", "ix_vouchers_id"):
            op.drop_index(op.f("ix_vouchers_id"), table_name="vouchers")
        op.drop_table("vouchers")