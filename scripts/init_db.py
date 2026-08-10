import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy_utils import database_exists, create_database
from app.db.session import engine, DATABASE_URL, SessionLocal
from app.db.base import Base
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.db.seed import seed_db

def init_db():
    if not database_exists(DATABASE_URL):
        print(f"Creating database: {DATABASE_URL}")
        create_database(DATABASE_URL)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
