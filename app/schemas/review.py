from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_item_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewUserInfo(BaseModel):
    id: str
    name: str
    photoprofil: Optional[str] = None

    class Config:
        from_attributes = True


class Review(BaseModel):
    id: str
    product_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    user: ReviewUserInfo

    class Config:
        from_attributes = True


class ProductRatingSummary(BaseModel):
    average_rating: float
    review_count: int