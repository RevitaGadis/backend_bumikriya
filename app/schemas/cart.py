from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.product import Product


class CartItem(BaseModel):
    id: int
    product_id: str
    quantity: int
    price: float
    subtotal: float
    product: Optional[Product] = None

    class Config:
        from_attributes = True


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


class Cart(BaseModel):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    items: List[CartItem] = []
    total_items: int = 0
    total_price: float = 0

    class Config:
        from_attributes = True
