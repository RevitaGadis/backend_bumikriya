from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.product import Product


class WishlistCreate(BaseModel):
    product_id: str


class Wishlist(BaseModel):
    id: int
    user_id: str
    product_id: str
    created_at: datetime
    product: Optional[Product] = None

    class Config:
        from_attributes = True
