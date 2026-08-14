from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class VoucherBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    discount_percent: Decimal = Decimal("0")
    max_discount: Optional[Decimal] = None
    min_purchase: Decimal = Decimal("0")
    quota: int = 0
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class VoucherCreate(VoucherBase):
    pass

class VoucherUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    discount_percent: Optional[Decimal] = None
    max_discount: Optional[Decimal] = None
    min_purchase: Optional[Decimal] = None
    quota: Optional[int] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class VoucherInDBBase(VoucherBase):
    id: str
    used_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Voucher(VoucherInDBBase):
    pass