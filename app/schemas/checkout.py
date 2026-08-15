from typing import Optional
from pydantic import BaseModel
from app.schemas.dashboard import PaymentMethod


class CheckoutRequest(BaseModel):
    shipping_address: str
    payment_method: PaymentMethod
    shipping_cost: float = 0
    voucher_code: Optional[str] = None