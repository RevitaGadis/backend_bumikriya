import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy_utils import database_exists, create_database
from app.db.session import DATABASE_URL


def init_db():
    if not database_exists(DATABASE_URL):
        print(f"Creating database: {DATABASE_URL}")
        create_database(DATABASE_URL)
    else:
        print("Database already exists")


if __name__ == "__main__":
    init_db()
