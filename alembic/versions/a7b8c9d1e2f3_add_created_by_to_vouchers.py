"""add created_by to vouchers

Revision ID: a7b8c9d1e2f3
Revises: f6a7b8c9d1e2
Create Date: 2026-08-14 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    columns = [col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Upgrade schema."""
    if _table_exists("vouchers") and not _column_exists("vouchers", "created_by"):
        op.add_column(
            "vouchers",
            sa.Column("created_by", sa.String(length=36), nullable=True),
        )
        op.create_foreign_key(
            "fk_vouchers_created_by",
            "vouchers",
            "users",
            ["created_by"],
            ["id"],
        )
        op.create_index(
            op.f("ix_vouchers_created_by"), "vouchers", ["created_by"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists("vouchers") and _column_exists("vouchers", "created_by"):
        op.drop_index(op.f("ix_vouchers_created_by"), table_name="vouchers")
        try:
            op.drop_constraint("fk_vouchers_created_by", "vouchers", type_="foreignkey")
        except Exception:
            pass
        op.drop_column("vouchers", "created_by")