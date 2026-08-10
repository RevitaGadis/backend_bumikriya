import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from sqlalchemy_utils import database_exists, create_database
from app.db.session import engine, DATABASE_URL, SessionLocal
from app.db.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.saving import Saving
from app.models.product import Product
from app.models.order import Order
from app.db.seed import seed_db


def migrate_db():
    inspector = inspect(engine)
    user_columns = [column["name"] for column in inspector.get_columns("users")]

    if "role_id" not in user_columns:
        print("Migrating users table: adding role_id column")
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN role_id INTEGER NULL"))

def init_db():
    if not database_exists(DATABASE_URL):
        print(f"Creating database: {DATABASE_URL}")
        create_database(DATABASE_URL)

    Base.metadata.create_all(bind=engine)
    migrate_db()

    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
