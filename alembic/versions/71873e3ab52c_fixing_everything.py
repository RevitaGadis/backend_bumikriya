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

    op.create_foreign_key(
        None,
        "reviews",
        "order_items",
        ["order_item_id"],
        ["id"],
    )

    op.add_column(
        "stores",
        sa.Column(
            "tagline",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "stores",
        sa.Column(
            "banner",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "stores",
        sa.Column(
            "shipping_policy",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "stores",
        sa.Column(
            "return_policy",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "stores",
        sa.Column(
            "custom_policy",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "stores",
        sa.Column(
            "tags",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_unique_constraint(
        "uq_user_vouchers_user_level",
        "user_vouchers",
        ["user_id", "level_code"],
    )

    op.create_unique_constraint(
        "uq_wishlists_user_product",
        "wishlists",
        ["user_id", "product_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_wishlists_user_product",
        "wishlists",
        type_="unique",
    )

    op.drop_constraint(
        "uq_user_vouchers_user_level",
        "user_vouchers",
        type_="unique",
    )

    op.drop_column("stores", "tags")
    op.drop_column("stores", "custom_policy")
    op.drop_column("stores", "return_policy")
    op.drop_column("stores", "shipping_policy")
    op.drop_column("stores", "banner")
    op.drop_column("stores", "tagline")

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