from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class ProductBrief(BaseModel):
    id: str
    name: str
    price: float
    image: str
    stock: int
    seller_id: str

    class Config:
        from_attributes = True


class RecipeMaterialCreate(BaseModel):
    category_id: str
    material_name: str
    quantity_needed: float = 1
    unit: Optional[str] = None
    note: Optional[str] = None
    suggested_product_id: Optional[str] = None


class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    category_id: Optional[str] = None
    materials: List[RecipeMaterialCreate]


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    category_id: Optional[str] = None
    materials: Optional[List[RecipeMaterialCreate]] = None


class RecipeMaterialOut(BaseModel):
    id: str
    material_name: str
    quantity_needed: float
    unit: Optional[str] = None
    note: Optional[str] = None
    suggested_product: Optional[ProductBrief] = None
    recommended_products: List[ProductBrief] = []

    class Config:
        from_attributes = True


class RecipeSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeDetail(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    materials: List[RecipeMaterialOut]

    class Config:
        from_attributes = True