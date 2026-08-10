from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "finsight-api")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0")

    DATABASE_USER: str = os.getenv("DATABASE_USER", "user")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "password")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", 3306))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "finsight")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    CSRF_SECRET: str = os.getenv("CSRF_SECRET", "your-csrf-secret")

    FIRST_USER_ADMIN_EMAIL: str = os.getenv("FIRST_USER_ADMIN_EMAIL", "admin@finsight.com")
    FIRST_USER_ADMIN_PASSWORD: str = os.getenv("FIRST_USER_ADMIN_PASSWORD", "admin123")

    class Config:
        case_sensitive = True

settings = Settings()
