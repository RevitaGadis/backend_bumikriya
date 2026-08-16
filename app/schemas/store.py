from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class StoreBase(BaseModel):
    store_name: str
    tagline: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    address: Optional[str] = None
    shipping_policy: Optional[str] = None
    return_policy: Optional[str] = None
    custom_policy: Optional[str] = None
    tags: Optional[str] = None


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    store_name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    address: Optional[str] = None
    shipping_policy: Optional[str] = None
    return_policy: Optional[str] = None
    custom_policy: Optional[str] = None
    tags: Optional[str] = None


class StoreInDBBase(StoreBase):
    id: str
    user_id: str
    is_approved: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Store(StoreInDBBase):
    pass


# ---------- Public store detail (GET /api/v1/stores/{store_id}) ----------


class StoreSeller(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str] = None


class StoreBadge(BaseModel):
    type: Optional[str] = None
    label: Optional[str] = None


class StoreLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    display_name: Optional[str] = None


class StoreProfile(BaseModel):
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    badge: Optional[StoreBadge] = None
    location: Optional[StoreLocation] = None


class StoreStatistics(BaseModel):
    rating: Optional[float] = None
    total_reviews: int = 0
    total_sales: int = 0
    sales_display: str = "0"
    active_since: Optional[int] = None
    total_products: int = 0


class StoreAboutTag(BaseModel):
    id: str
    name: str


class StoreAbout(BaseModel):
    title: str = "Our Story"
    description: Optional[str] = None
    tags: List[StoreAboutTag] = []


class StoreRule(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class StoreShopRules(BaseModel):
    shipping: Optional[StoreRule] = None
    returns: Optional[StoreRule] = None
    commissions: Optional[StoreRule] = None


class StoreDetail(BaseModel):
    id: str
    name: str
    slug: str
    seller: StoreSeller
    profile: StoreProfile
    statistics: StoreStatistics
    about: StoreAbout
    shop_rules: StoreShopRules = StoreShopRules()
    is_following: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------- Store products (GET /api/v1/stores/{store_id}/products) ----------


class StoreProductItem(BaseModel):
    id: str
    name: str
    slug: str
    price: float
    currency: str = "USD"
    thumbnail_url: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: int = 0
    is_favorite: bool = False


class StorePagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class StoreProductListResponse(BaseModel):
    data: List[StoreProductItem] = []
    pagination: StorePagination


# ---------- Store reviews (GET /api/v1/stores/{store_id}/reviews) ----------


class StoreReviewItem(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: Optional[float] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class StoreReviewListResponse(BaseModel):
    data: List[StoreReviewItem] = []
    pagination: StorePagination

class StoreWithRating(StoreInDBBase):
    average_rating: float = 0.0
    review_count: int = 0