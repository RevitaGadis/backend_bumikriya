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


class VoucherBrief(BaseModel):
    id: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    discount_percent: float = 0

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    user_id: str
    order_number: str
    subtotal: float
    shipping_cost: float
    discount: float = 0
    total_amount: float
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    items: List[OrderItem] = []
    payment: Optional[Payment] = None
    voucher: Optional[VoucherBrief] = None

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None


class OrderStatusInfo(BaseModel):
    code: str
    label: str


class ShippingAddressInfo(BaseModel):
    recipient_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None


class CustomerInfo(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None
    avatar: Optional[str] = None
    shipping_address: Optional[ShippingAddressInfo] = None


class OrderItemDetail(BaseModel):
    id: int
    product_id: Optional[str] = None
    product_name: str
    sku: Optional[str] = None
    image: Optional[str] = None
    price: float
    quantity: int
    subtotal: float


class PaymentDetail(BaseModel):
    subtotal: float
    shipping_cost: float
    discount: float = 0
    total: float
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    paid_at: Optional[datetime] = None
    voucher: Optional[VoucherBrief] = None


class ShippingDetail(BaseModel):
    courier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_status: Optional[str] = None


class StatusHistoryItem(BaseModel):
    status: str
    label: str
    created_at: Optional[datetime] = None


class OrderDetail(BaseModel):
    id: int
    order_number: str
    status: OrderStatusInfo
    customer: CustomerInfo
    items: List[OrderItemDetail] = []
    payment: PaymentDetail
    shipping: ShippingDetail
    status_history: List[StatusHistoryItem] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderDetailResponse(BaseModel):
    success: bool
    data: OrderDetail

class OrderStatusUpdate(BaseModel):
    status: OrderStatus