"""repair product columns

Revision ID: 7d9c2e4f6a01
Revises: 52400713a1fc
Create Date: 2026-08-16 17:46:00.000000

"""
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7d9c2e4f6a01"
down_revision: Union[str, Sequence[str], None] = "52400713a1fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _fk_exists(table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


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


def _first_id(table_name: str) -> Optional[str]:
    return op.get_bind().execute(sa.text(f"SELECT id FROM {table_name} ORDER BY id LIMIT 1")).scalar()


def _has_nulls(column_name: str) -> bool:
    return bool(
        op.get_bind()
        .execute(sa.text(f"SELECT EXISTS (SELECT 1 FROM products WHERE {column_name} IS NULL)"))
        .scalar()
    )


def _has_invalid_references(column_name: str, referenced_table: str) -> bool:
    return bool(
        op.get_bind()
        .execute(
            sa.text(
                f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM products p
                    LEFT JOIN {referenced_table} r ON r.id = p.{column_name}
                    WHERE p.{column_name} IS NOT NULL AND r.id IS NULL
                )
                """
            )
        )
        .scalar()
    )


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    if not _column_exists("products", "description"):
        op.add_column("products", sa.Column("description", sa.Text(), nullable=True))

    if not _column_exists("products", "is_active"):
        op.add_column(
            "products",
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        )

    if not _column_exists("products", "seller_id"):
        op.add_column("products", sa.Column("seller_id", sa.String(length=36), nullable=True))
    fallback_seller_id = _first_id("users")
    if fallback_seller_id:
        conn.execute(
            sa.text("UPDATE products SET seller_id = :seller_id WHERE seller_id IS NULL"),
            {"seller_id": fallback_seller_id},
        )
    if not _has_nulls("seller_id"):
        op.alter_column("products", "seller_id", existing_type=sa.String(length=36), nullable=False)
    if not _index_exists("products", "ix_products_seller_id"):
        op.create_index(op.f("ix_products_seller_id"), "products", ["seller_id"], unique=False)
    if (
        not _fk_exists("products", "fk_products_seller_id_users")
        and not _equivalent_fk_exists("products", "seller_id", "users", "id")
        and not _has_invalid_references("seller_id", "users")
    ):
        op.create_foreign_key(
            "fk_products_seller_id_users",
            "products",
            "users",
            ["seller_id"],
            ["id"],
        )

    if not _column_exists("products", "category_id"):
        op.add_column("products", sa.Column("category_id", sa.String(length=36), nullable=True))
    fallback_category_id = _first_id("categories")
    if fallback_category_id:
        conn.execute(
            sa.text("UPDATE products SET category_id = :category_id WHERE category_id IS NULL"),
            {"category_id": fallback_category_id},
        )
    if not _has_nulls("category_id"):
        op.alter_column("products", "category_id", existing_type=sa.String(length=36), nullable=False)
    if not _index_exists("products", "ix_products_category_id"):
        op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)
    if (
        not _fk_exists("products", "fk_products_category_id_categories")
        and not _equivalent_fk_exists("products", "category_id", "categories", "id")
        and not _has_invalid_references("category_id", "categories")
    ):
        op.create_foreign_key(
            "fk_products_category_id_categories",
            "products",
            "categories",
            ["category_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
