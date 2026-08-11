import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
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
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.whitelist import Whitelist
from app.db.seed import seed_db


def migrate_db():
    inspector = inspect(engine)
    user_columns = [column["name"] for column in inspector.get_columns("users")]

    if "role_id" not in user_columns:
        print("Migrating users table: adding role_id column")
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN role_id VARCHAR(36) NULL"))

    table_names = inspector.get_table_names()
    if "orders" in table_names:
        order_columns = [column["name"] for column in inspector.get_columns("orders")]
        if "user_id" not in order_columns:
            print("Migrating orders table: dropping old schema (orders/order_items/payments)")
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE IF EXISTS payments"))
                connection.execute(text("DROP TABLE IF EXISTS order_items"))
                connection.execute(text("DROP TABLE IF EXISTS orders"))

def init_db():
    db_url = make_url(DATABASE_URL)
    print(f"Connecting to PostgreSQL at {db_url.host}:{db_url.port or 5432} (database: {db_url.database})")

    db_ready = False
    for attempt in range(1, 16):
        try:
            if not database_exists(DATABASE_URL):
                print("Database does not exist yet, creating it...")
                create_database(DATABASE_URL)
            db_ready = True
            break
        except OperationalError as exc:
            print(f"Database not ready (attempt {attempt}/15) at {db_url.host}: {exc}")
            time.sleep(5)

    if not db_ready:
        raise RuntimeError("Could not connect to the database after 15 attempts")

    Base.metadata.create_all(bind=engine)
    migrate_db()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
