from typing import Optional
from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
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