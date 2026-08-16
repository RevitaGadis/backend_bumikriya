from pathlib import Path
import logging
from typing import Any
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.endpoints import auth, checkout, home, category, admin, seller, user, product, order, wishlist, cart, notification,payment, stores, voucher, review, recipe

logger = logging.getLogger("uvicorn.error")


def _sanitize_binary(obj: Any) -> Any:
    if isinstance(obj, bytes):
        return f"<binary data: {len(obj)} bytes>"
    if isinstance(obj, dict):
        return {k: _sanitize_binary(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_binary(v) for v in obj]
    return obj


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": _sanitize_binary(exc.errors())},
    )

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        settings.FRONTEND_URL,
        "https://three-bug-coder.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/v1/auth",        tags=["Auth"])
app.include_router(checkout.router,    prefix="/api/v1/checkout",    tags=["Checkout"])
app.include_router(home.router,        prefix="/api/v1/home",        tags=["Home"])
app.include_router(category.router,    prefix="/api/v1/categories",  tags=["Categories"])
app.include_router(seller.router,      prefix="/api/v1/seller",      tags=["Seller"])
app.include_router(user.router,        prefix="/api/v1/user",        tags=["User"])
app.include_router(admin.router,       prefix="/api/v1/admin",       tags=["Admin"])
app.include_router(product.router,     prefix="/api/v1/products",    tags=["Products"])
app.include_router(order.router,       prefix="/api/v1/orders",      tags=["Orders"])
app.include_router(wishlist.router,   prefix="/api/v1/wishlists", tags=["Wishlist"])
app.include_router(stores.router,     prefix="/api/v1/stores",    tags=["Stores"])
app.include_router(cart.router,        prefix="/api/v1/cart",        tags=["Cart"])
app.include_router(notification.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(notification.ws_router)
app.include_router(payment.router, prefix="/payments", tags=["Payments"])
app.include_router(voucher.router,    prefix="/api/v1/vouchers",   tags=["Vouchers"])
app.include_router(review.router, prefix="/api/v1", tags=["Reviews"])
app.include_router(recipe.router, prefix="/recipes", tags=["Recipes"])

@app.get("/")
async def root():
    return {"message": "Welcome to BumiKriya API!"}

@app.on_event("startup")
async def _log_email_config():
    from app.services.email_service import _gmail_configured
    logger.info(
        "Email providers configured — gmail=%s resend=%s smtp=%s (host=%s)",
        _gmail_configured(),
        bool(settings.RESEND_API_KEY),
        bool(settings.SMTP_HOST),
        settings.SMTP_HOST,
    )


@app.on_event("startup")
async def _seed_default_membership_types():
    from app.db.session import SessionLocal
    from app.services.membership_service import ensure_default_membership_types
    db = SessionLocal()
    try:
        ensure_default_membership_types(db)
    finally:
        db.close()
