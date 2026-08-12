from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class AdminAccountItem(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: Optional[str] = None
    role: Optional[str] = None
    status: str
    is_verified: bool


class AdminAccountPagination(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int


class AdminAccountListData(BaseModel):
    items: List[AdminAccountItem]
    pagination: AdminAccountPagination


class AdminAccountListResponse(BaseModel):
    success: bool
    message: str
    data: AdminAccountListData


class AdminAccountSummaryData(BaseModel):
    total_accounts: int
    total_verified: int
    role_distribution: Dict[str, int]
    status_distribution: Dict[str, int]


class AdminAccountSummaryResponse(BaseModel):
    success: bool
    data: AdminAccountSummaryData


class AdminAccountDetail(AdminAccountItem):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminAccountDetailResponse(BaseModel):
    success: bool
    message: str
    data: AdminAccountDetail


class AdminAccountCreateResponse(BaseModel):
    success: bool
    message: str
    data: AdminAccountDetail


class AdminAccountUpdateResponse(BaseModel):
    success: bool
    message: str
    data: AdminAccountDetail


class AdminAccountStatusUpdate(BaseModel):
    status: str
