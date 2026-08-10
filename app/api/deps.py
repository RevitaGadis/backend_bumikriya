from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from redis import Redis, ConnectionError as RedisConnectionError
from app.core.redis_mock import RedisMock

# Global instance for in-memory fallback
_redis_mock = RedisMock()

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import decode_token
from app.models.user import User
from app.schemas.token import TokenPayload


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), request: Request = None
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None
    # Try to get token from Authorization header first
    if request and request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization")
        parts = auth_header.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
            token = parts[1]
    # If not in header, try to get token from cookie
    if not token and request and "access_token" in request.cookies:
        token = request.cookies["access_token"]
    
    # If still no token, raise exception
    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        user_id = payload.sub
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin and (not current_user.role or current_user.role.name != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user

def get_current_admin_or_seller(current_user: User = Depends(get_current_user)) -> User:
    if current_user.is_admin or (current_user.role and current_user.role.name in ("admin", "seller")):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin or seller access required",
    )

def get_current_seller(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.role or current_user.role.name != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller access required",
        )
    return current_user

def get_current_regular_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.role or current_user.role.name != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )
    return current_user

import logging

logger = logging.getLogger(__name__)

def get_redis_client() -> Redis:
    client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD or None)
    try:
        client.ping()
        return client
    except RedisConnectionError:
        logger.warning("Redis server not found at %s:%s. Falling back to in-memory storage.", 
                       settings.REDIS_HOST, settings.REDIS_PORT)
        return _redis_mock
