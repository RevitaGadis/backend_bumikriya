from typing import List, Optional
from pydantic import BaseModel
from app.schemas.dashboard import PaymentMethod


class CheckoutRequest(BaseModel):
    cart_item_ids: List[int] 
    shipping_address: str
    payment_method: PaymentMethod
    shipping_cost: float = 0
    voucher_code: Optional[str] = None