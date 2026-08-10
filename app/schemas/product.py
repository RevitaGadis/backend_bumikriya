from typing import Optional
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    price: float = 0
    image: str
    stock: int = 0
    is_active: Optional[bool] = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None

class ProductInDBBase(ProductBase):
    id: int

    class Config:
        from_attributes = True

class Product(ProductInDBBase):
    pass
