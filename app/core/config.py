from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote
from sqlalchemy.engine import make_url
import os

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / "env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)
else:
    load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "bumikriya")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0")

    DATABASE_USER: str = os.getenv("DATABASE_USER", os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres")))
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "AzkaSaadi07")))
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "localhost")))
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", os.getenv("PGPORT", os.getenv("POSTGRES_PORT", 5432))))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "bumikriya")))

    @property
    def DATABASE_URL(self) -> str:
        raw = os.getenv("DATABASE_URL", "").strip() or os.getenv("PGURL", "").strip()
        if raw:
            url = make_url(raw).set(drivername="postgresql+psycopg2")
            return url.render_as_string(hide_password=False)
        return (
            f"postgresql+psycopg2://{quote(self.DATABASE_USER)}:{quote(self.DATABASE_PASSWORD)}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "False").lower() in ("1", "true", "yes", "on")
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")

    CSRF_SECRET: str = os.getenv("CSRF_SECRET", "your-csrf-secret")

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://three-bug-coder.vercel.app")

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))
    BASE_URL: str = os.getenv("BASE_URL", "https://backendbumikriya-production.up.railway.app")

    FIRST_USER_ADMIN_EMAIL: str = os.getenv("FIRST_USER_ADMIN_EMAIL")
    FIRST_USER_ADMIN_PASSWORD: str = os.getenv("FIRST_USER_ADMIN_PASSWORD")

    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_FROM: str = os.getenv("SMTP_FROM")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() in ("1", "true", "yes", "on")

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    RESEND_FROM: str = os.getenv("RESEND_FROM", "Bumikriya <onboarding@resend.dev>")

    RESET_CODE_EXPIRE_MINUTES: int = int(os.getenv("RESET_CODE_EXPIRE_MINUTES", 10))
    VERIFY_EMAIL_EXPIRE_MINUTES: int = int(os.getenv("VERIFY_EMAIL_EXPIRE_MINUTES", 24 * 60))

    class Config:
        case_sensitive = True

settings = Settings()
