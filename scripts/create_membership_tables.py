import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.db.base import Base
from app.models import membership  # noqa: F401  (register membership tables on Base.metadata)
from sqlalchemy import inspect


def create_membership_tables() -> None:
    membership_tables = {
        Base.metadata.tables["membership_types"],
        Base.metadata.tables["user_memberships"],
        Base.metadata.tables["membership_benefits"],
    }

    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    to_create = [t for t in membership_tables if t.name not in existing]

    if not to_create:
        print("Membership tables already exist, skipping.")
        return

    print(f"Creating missing membership tables: {[t.name for t in to_create]}")
    Base.metadata.create_all(bind=engine, tables=to_create, checkfirst=True)
    print("Done.")


if __name__ == "__main__":
    create_membership_tables()
