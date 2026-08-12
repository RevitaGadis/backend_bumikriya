from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class StoreBase(BaseModel):
    store_name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    address: Optional[str] = None


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    store_name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    address: Optional[str] = None


class StoreInDBBase(StoreBase):
    id: str
    user_id: str
    is_approved: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Store(StoreInDBBase):
    pass