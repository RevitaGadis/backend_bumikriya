"""compat merge store profile and recipes heads

Revision ID: 52400713a1fc
Revises: 5ed80f2548af
Create Date: 2026-08-16 17:45:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "52400713a1fc"
down_revision: Union[str, Sequence[str], None] = "5ed80f2548af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This revision was previously deployed/stamped, but the migration file was
    # missing from the repository. Keep it as a no-op bridge so Alembic can
    # continue upgrading databases that already point at this revision.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
