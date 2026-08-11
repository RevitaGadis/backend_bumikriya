from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 15, "keepalives": 1, "keepalives_idle": 30, "keepalives_interval": 10, "keepalives_count": 5},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)