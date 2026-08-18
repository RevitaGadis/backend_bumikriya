"""fixing everything

Revision ID: 71873e3ab52c
Revises: 7d9c2e4f6a01
Create Date: 2026-08-18 08:12:06.207695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "71873e3ab52c"
down_revision: Union[str, Sequence[str], None] = "7d9c2e4f6a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _unique_constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {uc["name"] for uc in inspector.get_unique_constraints(table_name)}


def _equivalent_fk_exists(
    table_name: str,
    column_name: str,
    referenced_table: str,
    referenced_column: str,
) -> bool:
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys(table_name):
        if (
            fk["constrained_columns"] == [column_name]
            and fk["referred_table"] == referenced_table
            and fk["referred_columns"] == [referenced_column]
        ):
            return True
    return False


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    if _column_exists("products", "is_featured"):
        op.drop_column(
            "products",
            "is_featured",
        )

    op.alter_column(
        "reviews",
        "order_item_id",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.BigInteger(),
        existing_nullable=False,
        postgresql_using="order_item_id::bigint",
    )

    if not _equivalent_fk_exists("reviews", "order_item_id", "order_items", "id"):
        op.create_foreign_key(
            None,
            "reviews",
            "order_items",
            ["order_item_id"],
            ["id"],
        )

    if not _column_exists("stores", "tagline"):
        op.add_column(
            "stores",
            sa.Column(
                "tagline",
                sa.String(length=255),
                nullable=True,
            ),
        )

    if not _column_exists("stores", "banner"):
        op.add_column(
            "stores",
            sa.Column(
                "banner",
                sa.String(length=255),
                nullable=True,
            ),
        )

    if not _column_exists("stores", "shipping_policy"):
        op.add_column(
            "stores",
            sa.Column(
                "shipping_policy",
                sa.Text(),
                nullable=True,
            ),
        )

    if not _column_exists("stores", "return_policy"):
        op.add_column(
            "stores",
            sa.Column(
                "return_policy",
                sa.Text(),
                nullable=True,
            ),
        )

    if not _column_exists("stores", "custom_policy"):
        op.add_column(
            "stores",
            sa.Column(
                "custom_policy",
                sa.Text(),
                nullable=True,
            ),
        )

    if not _column_exists("stores", "tags"):
        op.add_column(
            "stores",
            sa.Column(
                "tags",
                sa.Text(),
                nullable=True,
            ),
        )

    if not _unique_constraint_exists("user_vouchers", "uq_user_vouchers_user_level"):
        op.create_unique_constraint(
            "uq_user_vouchers_user_level",
            "user_vouchers",
            ["user_id", "level_code"],
        )

    if not _unique_constraint_exists("wishlists", "uq_wishlists_user_product"):
        op.create_unique_constraint(
            "uq_wishlists_user_product",
            "wishlists",
            ["user_id", "product_id"],
        )


def downgrade() -> None:
    """Downgrade schema."""

    if _unique_constraint_exists("wishlists", "uq_wishlists_user_product"):
        op.drop_constraint(
            "uq_wishlists_user_product",
            "wishlists",
            type_="unique",
        )

    if _unique_constraint_exists("user_vouchers", "uq_user_vouchers_user_level"):
        op.drop_constraint(
            "uq_user_vouchers_user_level",
            "user_vouchers",
            type_="unique",
        )

    for _col in ("tags", "custom_policy", "return_policy", "shipping_policy", "banner", "tagline"):
        if _column_exists("stores", _col):
            op.drop_column("stores", _col)

    if _equivalent_fk_exists("reviews", "order_item_id", "order_items", "id"):
        op.drop_constraint(
            None,
            "reviews",
            type_="foreignkey",
        )

    op.alter_column(
        "reviews",
        "order_item_id",
        existing_type=sa.BigInteger(),
        type_=sa.VARCHAR(length=36),
        existing_nullable=False,
    )
    if not _column_exists("products", "is_featured"):
        op.add_column(
            "products",
            sa.Column(
                "is_featured",
                sa.BOOLEAN(),
                server_default=sa.text("false"),
                autoincrement=False,
                nullable=False,
            ),
        )

    op.drop_column(
        "products",
        "updated_at",
    )

    op.drop_column(
        "products",
        "created_at",
    )
    op.drop_column(
        "orders",
        "updated_at",
    )