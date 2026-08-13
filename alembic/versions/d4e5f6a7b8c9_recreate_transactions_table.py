"""recreate transactions table

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-08-13 21:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _transaction_type_enum():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        enum_type = postgresql.ENUM(
            "income",
            "expense",
            name="transactiontype",
            create_type=False,
        )
        enum_type.create(bind, checkfirst=True)
        return enum_type
    return sa.Enum("income", "expense", name="transactiontype")


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("transactions"):
        op.create_table(
            "transactions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column(
                "transaction_date",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.Column("category_id", sa.String(length=36), nullable=False),
            sa.Column("transaction_type", _transaction_type_enum(), nullable=False),
            sa.Column("note", sa.String(length=500), nullable=True),
            sa.Column("user_id", sa.String(length=36), nullable=True),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _index_exists("transactions", "ix_transactions_id"):
        op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
    if not _index_exists("transactions", "ix_transactions_category_id"):
        op.create_index(
            op.f("ix_transactions_category_id"),
            "transactions",
            ["category_id"],
            unique=False,
        )
    if not _index_exists("transactions", "ix_transactions_user_id"):
        op.create_index(
            op.f("ix_transactions_user_id"),
            "transactions",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
