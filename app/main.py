from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.endpoints import auth, home, transaction, category, admin, saving, seller, user, product

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
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
app.include_router(saving.router,      prefix="/api/v1/savings",     tags=["Savings"])
app.include_router(seller.router,      prefix="/api/v1/seller",      tags=["Seller"])
app.include_router(user.router,        prefix="/api/v1/user",        tags=["User"])
app.include_router(admin.router,       prefix="/api/v1/admin",       tags=["Admin"])
app.include_router(product.router,     prefix="/api/v1/products",    tags=["Products"])

@app.get("/")
async def root():
    return {"message": "Welcome to Finsight API!"}
