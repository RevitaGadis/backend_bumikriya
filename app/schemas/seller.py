from typing import Optional
from pydantic import BaseModel, EmailStr


class SellerUser(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str


class SellerInfo(BaseModel):
    id: str
    store_name: Optional[str] = None
    store_slug: Optional[str] = None
    status: str


class SellerMeData(BaseModel):
    user: SellerUser
    seller: SellerInfo


class SellerMeResponse(BaseModel):
    success: bool
    message: str
    data: SellerMeData
