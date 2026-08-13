from datetime import timedelta
import json
import secrets
from urllib.parse import quote
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
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash, decode_token
from app.api import deps
from app.services import user_service
from app.services.email_service import send_email, get_last_email_error
from app.schemas.user import UserCreate, UserLogin, ForgotPasswordRequest, VerifyResetCodeRequest, ResetPasswordRequest, MeResponse
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
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=access_token_expires.total_seconds(),
        expires=access_token_expires.total_seconds(),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=refresh_token_expires.total_seconds(),
        expires=refresh_token_expires.total_seconds(),
    )

    redis_client.setex(f"refresh_token:{user.id}", refresh_token_expires, refresh_token)

    return access_token, refresh_token

def _login_response(response: Response, user: User, redis_client: Redis) -> dict[str, Any]:
    access_token, refresh_token = _set_auth_cookies(response, user, redis_client)
    return {
        "message": "Login successful",
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
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
    if not redirect_uri or "localhost:8000" in redirect_uri:
        redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/auth/google/callback"
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

    access_token, refresh_token = _set_auth_cookies(response, user, redis_client)
    role = user.role.name if user.role else ("admin" if user.is_admin else "user")
    user_payload = quote(
        json.dumps(
            {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": role,
            },
            ensure_ascii=False,
        )
    )
    return RedirectResponse(
        url=(
            f"{settings.FRONTEND_URL}/login"
            f"?token={access_token}&user={user_payload}&status=success"
        )
    )

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

@router.get("/me", response_model=MeResponse)
def read_me(current_user: User = Depends(deps.get_current_user)) -> Any:
    role = current_user.role.name if current_user.role else ("admin" if current_user.is_admin else "user")
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": role,
    }

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
    redis_client: Redis = Depends(deps.get_redis_client),
    request: Request,
    user_in: UserCreate
) -> Any:
    user = user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )

    token = secrets.token_urlsafe(32)
    pending = {
        "name": user_in.name,
        "email": user_in.email,
        "hashed_password": get_password_hash(user_in.password),
    }
    expires = settings.VERIFY_EMAIL_EXPIRE_MINUTES * 60
    redis_client.setex(f"verify_email:{token}", expires, json.dumps(pending))
    redis_client.setex(f"verify_email_user:{user_in.email}", expires, token)

    verify_url = (
        str(request.base_url).rstrip("/")
        + "/api/v1/auth/verify-email?token="
        + token
    )

    email_sent = send_email(
        to_email=user_in.email,
        subject="Verifikasi Email Anda",
        body_html=(
            "<p>Halo <strong>%s</strong>,</p>"
            "<p>Terima kasih telah mendaftar. Klik tombol di bawah untuk memverifikasi email Anda:</p>"
            "<p style='text-align:center;margin:24px 0'>"
            "<a href='%s' style='display:inline-block;padding:12px 24px;background-color:#16a34a;color:#ffffff;"
            "text-decoration:none;border-radius:6px;font-weight:bold'>Verifikasi Email</a></p>"
            "<p>Jika tombol tidak berfungsi, salin dan buka link berikut di browser Anda:</p>"
            "<p><a href='%s'>%s</a></p>"
            "<p>Link ini berlaku selama %s menit. Jangan bagikan link ini kepada siapa pun.</p>"
        ) % (
            user_in.name,
            verify_url,
            verify_url,
            verify_url,
            settings.VERIFY_EMAIL_EXPIRE_MINUTES,
        ),
        body_text=(
            f"Halo {user_in.name}, verifikasi email Anda dengan membuka link berikut: {verify_url} "
            f"(berlaku {settings.VERIFY_EMAIL_EXPIRE_MINUTES} menit)"
        ),
        use_resend=False,
    )
    if not email_sent:
        email_error = get_last_email_error()
        detail = "Registrasi diterima, tetapi gagal mengirim email verifikasi. Silakan gunakan 'Kirim Ulang Verifikasi'."
        if email_error:
            detail += f" ({email_error[:200]})"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )

    return {
        "message": "Registrasi berhasil. Silakan verifikasi email Anda melalui tautan yang dikirim ke email Anda."
    }

@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client),
) -> RedirectResponse:
    stored = redis_client.get(f"verify_email:{token}")
    if stored is None:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?status=verification_failed")

    stored_value = stored.decode("utf-8") if isinstance(stored, bytes) else stored
    try:
        pending = json.loads(stored_value)
    except (json.JSONDecodeError, TypeError):
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?status=verification_failed")

    email = pending.get("email")
    if user_service.get_user_by_email(db, email=email):
        redis_client.delete(f"verify_email:{token}")
        redis_client.delete(f"verify_email_user:{email}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?status=email_already_registered")

    user_service.create_user_with_password(
        db,
        name=pending.get("name"),
        email=email,
        hashed_password=pending.get("hashed_password"),
    )

    redis_client.delete(f"verify_email:{token}")
    redis_client.delete(f"verify_email_user:{email}")
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?status=email_verified")

@router.post("/resend-verification")
async def resend_verification_email(
    *,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client),
    request: Request,
    body: ForgotPasswordRequest,
) -> Any:
    email = body.email
    user = user_service.get_user_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar dan terverifikasi",
        )

    token = redis_client.get(f"verify_email_user:{email}")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak ada registrasi yang menunggu verifikasi",
        )
    token_value = token.decode("utf-8") if isinstance(token, bytes) else token

    stored = redis_client.get(f"verify_email:{token_value}")
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tautan verifikasi sudah kedaluwarsa. Silakan daftar ulang.",
        )

    stored_value = stored.decode("utf-8") if isinstance(stored, bytes) else stored
    try:
        pending = json.loads(stored_value)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tautan verifikasi tidak valid. Silakan daftar ulang.",
        )

    verify_url = (
        str(request.base_url).rstrip("/")
        + "/api/v1/auth/verify-email?token="
        + token_value
    )

    email_sent = send_email(
        to_email=email,
        subject="Verifikasi Email Anda",
        body_html=(
            "<p>Halo <strong>%s</strong>,</p>"
            "<p>Berikut tautan verifikasi email Anda:</p>"
            "<p style='text-align:center;margin:24px 0'>"
            "<a href='%s' style='display:inline-block;padding:12px 24px;background-color:#16a34a;color:#ffffff;"
            "text-decoration:none;border-radius:6px;font-weight:bold'>Verifikasi Email</a></p>"
            "<p>Jika tombol tidak berfungsi, salin dan buka link berikut di browser Anda:</p>"
            "<p><a href='%s'>%s</a></p>"
            "<p>Link ini berlaku selama %s menit. Jangan bagikan link ini kepada siapa pun.</p>"
        ) % (
            pending.get("name"),
            verify_url,
            verify_url,
            verify_url,
            settings.VERIFY_EMAIL_EXPIRE_MINUTES,
        ),
        body_text=(
            f"Halo {pending.get('name')}, verifikasi email Anda dengan membuka link berikut: {verify_url} "
            f"(berlaku {settings.VERIFY_EMAIL_EXPIRE_MINUTES} menit)"
        ),
        use_resend=False,
    )
    if not email_sent:
        email_error = get_last_email_error()
        detail = "Gagal mengirim email verifikasi. Silakan coba lagi nanti."
        if email_error:
            detail += f" ({email_error[:200]})"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )

    return {"message": "Tautan verifikasi telah dikirim ulang ke email Anda"}

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
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=access_token_expires.total_seconds(),
        expires=access_token_expires.total_seconds(),
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=refresh_token_expires.total_seconds(),
        expires=refresh_token_expires.total_seconds(),
    )

    return {
        "message": "Token refreshed successfully",
        "token_type": "bearer",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }

@router.post("/forgot-password")
async def forgot_password(
    *,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client),
    body: ForgotPasswordRequest,
) -> Any:
    user = user_service.get_user_by_email(db, email=body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email tidak terdaftar",
        )

    code = f"{secrets.randbelow(1000000):06d}"
    redis_client.setex(
        f"reset_code:{body.email.lower()}",
        settings.RESET_CODE_EXPIRE_MINUTES * 60,
        code,
    )

    email_sent = send_email(
        to_email=user.email,
        subject="Kode Verifikasi Reset Password",
        body_html=(
            "<p>Halo <strong>%s</strong>,</p>"
            "<p>Kode verifikasi untuk mereset password Anda adalah:</p>"
            "<h2 style='letter-spacing:4px'>%s</h2>"
            "<p>Kode ini berlaku selama %s menit. Jangan bagikan kode ini kepada siapa pun.</p>"
        ) % (user.name, code, settings.RESET_CODE_EXPIRE_MINUTES),
        body_text=f"Kode verifikasi reset password Anda: {code} (berlaku {settings.RESET_CODE_EXPIRE_MINUTES} menit)",
    )
    if not email_sent:
        email_error = get_last_email_error()
        detail = "Gagal mengirim kode verifikasi. Silakan coba lagi nanti."
        if email_error:
            detail += f" ({email_error[:200]})"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )

    return {"message": "Kode verifikasi telah dikirim ke email Anda"}

@router.post("/verify-reset-code")
async def verify_reset_code(
    *,
    response: Response,
    redis_client: Redis = Depends(deps.get_redis_client),
    body: VerifyResetCodeRequest,
) -> Any:
    stored = redis_client.get(f"reset_code:{body.email.lower()}")
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kode verifikasi tidak ditemukan atau sudah kedaluwarsa",
        )
    stored_value = stored.decode("utf-8") if isinstance(stored, bytes) else stored
    if stored_value != body.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kode verifikasi salah",
        )

    reset_token = secrets.token_urlsafe(32)
    redis_client.setex(
        f"reset_verified:{reset_token}",
        settings.RESET_CODE_EXPIRE_MINUTES * 60,
        body.email.lower(),
    )
    response.set_cookie(
        key="reset_token",
        value=reset_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.RESET_CODE_EXPIRE_MINUTES * 60,
    )

    return {"message": "Kode verifikasi valid", "reset_token": reset_token}

@router.post("/reset-password")
async def reset_password(
    *,
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    redis_client: Redis = Depends(deps.get_redis_client),
    body: ResetPasswordRequest,
) -> Any:
    reset_token = request.cookies.get("reset_token") or body.reset_token
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifikasi email dan kode terlebih dahulu",
        )

    stored_email = redis_client.get(f"reset_verified:{reset_token}")
    if stored_email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kode verifikasi tidak ditemukan atau sudah kedaluwarsa",
        )
    email = stored_email.decode("utf-8") if isinstance(stored_email, bytes) else stored_email

    user = user_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email tidak terdaftar",
        )

    user_service.update_password(db, user, body.password)
    redis_client.delete(f"reset_code:{email}")
    redis_client.delete(f"reset_verified:{reset_token}")
    response.delete_cookie(key="reset_token")

    return {"message": "Password berhasil direset"}
