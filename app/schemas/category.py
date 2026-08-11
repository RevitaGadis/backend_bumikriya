from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None

class CategoryInDBBase(CategoryBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Category(CategoryInDBBase):
    pass
