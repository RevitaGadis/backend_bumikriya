from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.endpoints import auth, home, transaction, category, admin, seller, user, product, order, wishlist, cart, notification

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
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
        "https://finsight-cc26-ps107.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/v1/auth",        tags=["Auth"])
app.include_router(home.router,        prefix="/api/v1/home",        tags=["Home"])
app.include_router(transaction.router, prefix="/api/v1",             tags=["Transactions"])
app.include_router(category.router,    prefix="/api/v1/categories",  tags=["Categories"])
app.include_router(seller.router,      prefix="/api/v1/seller",      tags=["Seller"])
app.include_router(user.router,        prefix="/api/v1/user",        tags=["User"])
app.include_router(admin.router,       prefix="/api/v1/admin",       tags=["Admin"])
app.include_router(product.router,     prefix="/api/v1/products",    tags=["Products"])
app.include_router(order.router,       prefix="/api/v1/orders",      tags=["Orders"])
app.include_router(wishlist.router,   prefix="/api/v1/wishlists",  tags=["Wishlist"])
app.include_router(cart.router,        prefix="/api/v1/cart",        tags=["Cart"])
app.include_router(notification.router, prefix="/api/v1/notifications", tags=["Notifications"])

@app.get("/")
async def root():
    return {"message": "Welcome to Finsight API!"}
