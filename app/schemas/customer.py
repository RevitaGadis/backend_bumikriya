from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class CustomerItem(BaseModel):
    id: str
    name: str
    email: str
    avatar: Optional[str] = None
    join_date: Optional[date] = None
    total_orders: int
    total_spent: float
    membership: Optional[str] = None


class CustomerStatistics(BaseModel):
    total_active_customers: int
    growth_percentage: float
    growth_period: str


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
    statistics: CustomerStatistics
    top_customer: Optional[TopCustomer]
    pagination: PaginationInfo


class CustomerListResponse(BaseModel):
    success: bool
    message: str
    data: CustomerListData
