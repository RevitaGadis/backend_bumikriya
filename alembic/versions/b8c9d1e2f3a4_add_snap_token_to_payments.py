"""add snap_token and redirect_url to payments

Revision ID: b8c9d1e2f3a4
Revises: a7b8c9d1e2f3
Create Date: 2026-08-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8c9d1e2f3a4"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    columns = [col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Upgrade schema."""
    if _table_exists("payments"):
        if not _column_exists("payments", "snap_token"):
            op.add_column(
                "payments",
                sa.Column("snap_token", sa.String(length=200), nullable=True),
            )
        if not _column_exists("payments", "redirect_url"):
            op.add_column(
                "payments",
                sa.Column("redirect_url", sa.String(length=500), nullable=True),
            )


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists("payments"):
        if _column_exists("payments", "redirect_url"):
            op.drop_column("payments", "redirect_url")
        if _column_exists("payments", "snap_token"):
            op.drop_column("payments", "snap_token")
