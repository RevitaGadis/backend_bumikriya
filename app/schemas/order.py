from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.dashboard import OrderStatus, PaymentMethod, PaymentStatus


class OrderItem(BaseModel):
    id: int
    product_id: str
    product_name: str
    price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True


class Payment(BaseModel):
    id: int
    method: PaymentMethod
    amount: float
    status: PaymentStatus
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    user_id: str
    order_number: str
    subtotal: float
    shipping_cost: float
    total_amount: float
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    items: List[OrderItem] = []
    payment: Optional[Payment] = None

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None
