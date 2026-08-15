from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_item_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class Review(BaseModel):
    id: str
    product_id: str
    user_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True