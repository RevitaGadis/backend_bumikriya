from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class CustomerItem(BaseModel):
    id: str
    name: str
    email: str
    initial: str
    avatar: Optional[str] = None
    joined_at: Optional[date] = None
    total_orders: int
    total_spent: float
    status: str
    membership: Optional[str] = None


class CustomerStats(BaseModel):
    active_customers: int
    growth_percentage: float


class TopCustomer(BaseModel):
    id: str
    name: str
    email: str
    avatar: Optional[str] = None
    membership: Optional[str] = None
    total_spent: float
    total_orders: int


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class CustomerListData(BaseModel):
    customers: List[CustomerItem]
    stats: CustomerStats
    top_customer: Optional[TopCustomer]
    pagination: PaginationInfo


class CustomerListResponse(BaseModel):
    success: bool
    data: CustomerListData


class CustomerMembership(BaseModel):
    name: str
    level: str


class CustomerSummary(BaseModel):
    total_spent: float
    total_orders: int
    average_order_value: float


class CustomerRecentOrder(BaseModel):
    id: int
    order_number: str
    order_date: str
    total: float
    status: str


class CustomerDetail(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    membership: Optional[CustomerMembership] = None
    joined_at: Optional[str] = None
    summary: Optional[CustomerSummary] = None
    recent_orders: List[CustomerRecentOrder] = []


class CustomerDetailResponse(BaseModel):
    success: bool
    message: str
    data: CustomerDetail


class CustomerUpdate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdateData(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None


class CustomerUpdateResponse(BaseModel):
    success: bool
    message: str
    data: CustomerUpdateData


class CustomerOrderHistoryItem(BaseModel):
    id: int
    order_number: str
    order_date: str
    total: float
    status: str
    status_label: str


class CustomerOrderHistoryResponse(BaseModel):
    success: bool
    message: str
    data: List[CustomerOrderHistoryItem]
    pagination: PaginationInfo


class AdminOrderDetailCustomer(BaseModel):
    id: str
    name: str


class AdminOrderDetailItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    subtotal: float


class AdminOrderDetailData(BaseModel):
    id: int
    order_number: str
    customer: AdminOrderDetailCustomer
    order_date: str
    status: str
    subtotal: float
    shipping_cost: float
    total: float
    items: List[AdminOrderDetailItem]


class AdminOrderDetailResponse(BaseModel):
    success: bool
    data: AdminOrderDetailData
