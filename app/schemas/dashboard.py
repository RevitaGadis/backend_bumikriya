from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class OrderStatus(str, Enum):
    DIPROSES = "DIPROSES"
    DIKIRIM = "DIKIRIM"
    SELESAI = "SELESAI"
    DIBATALKAN = "DIBATALKAN"


class PaymentMethod(str, Enum):
    CASH = "CASH"
    TRANSFER = "TRANSFER"
    OVO = "OVO"
    GOPAY = "GOPAY"
    DANA = "DANA"
    SHOPEEPAY = "SHOPEEPAY"
    COD = "COD"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class AdminSummary(BaseModel):
    total_seller: int
    pesanan_baru: int
    produk_aktif: int


class TopSellerItem(BaseModel):
    seller_id: str
    seller_name: str
    total_orders: int
    total_products_sold: int
    total_revenue: int


class LatestOrderItem(BaseModel):
    order_id: str
    customer_name: str
    seller_name: str
    total_amount: int
    status: str
    created_at: Optional[str]


class AdminDashboardData(BaseModel):
    summary: AdminSummary
    top_sellers: List[TopSellerItem]
    latest_orders: List[LatestOrderItem]


class AdminDashboard(BaseModel):
    success: bool
    message: str
    data: AdminDashboardData
