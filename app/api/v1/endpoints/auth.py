from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from redis import Redis
from jose import JWTError
from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config as StarletteEnvConfig

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password, decode_token
from app.api import deps
from app.services import user_service
from app.schemas.user import UserCreate, UserLogin
from app.schemas.token import TokenPayload 
from app.models.user import User

router = APIRouter()

_oauth_env = StarletteEnvConfig(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
})
oauth = OAuth(_oauth_env)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def _set_auth_cookies(response: Response, user: User, redis_client: Redis) -> None:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=access_token_expires.seconds,
        expires=access_token_expires.seconds,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=refresh_token_expires.total_seconds(),
        expires=refresh_token_expires.total_seconds(),
    )

    redis_client.setex(f"refresh_token:{user.id}", refresh_token_expires, refresh_token)

def _login_response(response: Response, user: User, redis_client: Redis) -> dict[str, Any]:
    _set_auth_cookies(response, user, redis_client)
    return {
        "message": "Login successful",
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }

@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured",
        )
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client),
) -> RedirectResponse:
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        print(f"Google OAuth error: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed")

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    email = userinfo.get("email")
    if not email:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=no_email")

    user = user_service.get_user_by_email(db, email=email)
    if not user:
        user = user_service.create_oauth_user(
            db, email=email, name=userinfo.get("name") or email
        )

    _set_auth_cookies(response, user, redis_client)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?status=success")

@router.post("/login")
async def login_for_access_token(
    response: Response,
    user_in: UserLogin,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client)
) -> Any:
    user = user_service.get_user_by_email(db, email=user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _login_response(response, user, redis_client)

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(deps.get_current_user), redis_client: Redis = Depends(deps.get_redis_client)) -> Any:
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    redis_client.delete(f"refresh_token:{current_user.id}")
    return {"message": "Logout successful"}

@router.post("/register")
async def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate
) -> Any:
    user = user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    user = user_service.create_user(db, user_in)
    return {"message": "User registered successfully"}

@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client)
) -> Any:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        payload = decode_token(refresh_token)
        if payload is None or payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )
        user_id = payload.sub
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in refresh token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )
    
    stored_refresh_token = redis_client.get(f"refresh_token:{user_id}")
    if stored_refresh_token is None or stored_refresh_token.decode("utf-8") != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user = user_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )

    redis_client.setex(f"refresh_token:{user.id}", refresh_token_expires, new_refresh_token)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=access_token_expires.seconds,
        expires=access_token_expires.seconds,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=refresh_token_expires.total_seconds(),
        expires=refresh_token_expires.total_seconds(),
    )

    return {"message": "Token refreshed successfully"}
