from enum import Enum
from typing import List

from pydantic import BaseModel


class OrderStatus(str, Enum):
    DIPROSES = "DIPROSES"
    DIKIRIM = "DIKIRIM"
    SELESAI = "SELESAI"
    DIBATALKAN = "DIBATALKAN"


class WeeklySalesItem(BaseModel):
    day: str
    total: int


class RecentOrderItem(BaseModel):
    order_number: str
    customer: str
    status: OrderStatus
    total: int


class AdminDashboard(BaseModel):
    total_sales: int
    new_orders: int
    active_products: int
    weekly_sales: List[WeeklySalesItem]
    recent_orders: List[RecentOrderItem]
