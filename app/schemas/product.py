from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ProductImage(BaseModel):
    id: str
    url: str
    is_primary: bool = False


class ProductCategory(BaseModel):
    id: str
    name: str


class ProductSpecification(BaseModel):
    name: str
    value: str


class ProductShippingInfo(BaseModel):
    processing_time: str
    shipping_method: str
    estimated_delivery: str


class ProductSeller(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str] = None
    badge: Optional[str] = None
    location: Optional[str] = None


class RelatedProduct(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    image_url: str


class ProductDetail(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    stock: int
    images: List[ProductImage] = []
    badges: List[str] = []
    category: Optional[ProductCategory] = None
    specifications: List[ProductSpecification] = []
    care_instructions: List[str] = []
    shipping_info: Optional[ProductShippingInfo] = None
    seller: Optional[ProductSeller] = None
    related_products: List[RelatedProduct] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0
    image: str
    color: str
    material: str
    fits: str
    stock: int = 0
    category_id: str
    is_active: Optional[bool] = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    fits: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None


class ProductStockUpdate(BaseModel):
    stock: int


class ProductInDBBase(ProductBase):
    id: str
    seller_id: str

    class Config:
        from_attributes = True


class Product(ProductInDBBase):
    pass