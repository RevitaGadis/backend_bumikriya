from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.services import product_service
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.core.uploads import save_upload
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Product])
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve products.
    """
    products = product_service.get_products(db, skip=skip, limit=limit)
    return products

@router.get("/{product_id}", response_model=Product)
def read_product(
    product_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve a single product.
    """
    product = product_service.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product

@router.post("/", response_model=Product)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Form(...),
    price: float = Form(0),
    stock: int = Form(0),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    """
    Create a new product with image upload. (Admin or seller only)
    """
    existing = product_service.get_product_by_name(db, name=name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this name already exists.",
        )

    image_path = save_upload(image) if image else "/images/products/default.jpg"
    product_in = ProductCreate(name=name, price=price, image=image_path, stock=stock, is_active=is_active)
    product = product_service.create_product(db, product=product_in)
    return product

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: str,
    *,
    db: Session = Depends(deps.get_db),
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    """
    Update a product with optional image upload. (Admin or seller only)
    """
    product = product_service.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    data = {}
    if name is not None:
        data["name"] = name
    if price is not None:
        data["price"] = price
    if stock is not None:
        data["stock"] = stock
    if is_active is not None:
        data["is_active"] = is_active
    if image is not None:
        data["image"] = save_upload(image)

    product_in = ProductUpdate(**data)
    product = product_service.update_product(db, product_id=product_id, product=product_in)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: str,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    """
    Delete a product. (Admin or seller only)
    """
    deleted = product_service.delete_product(db, product_id=product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return {"message": "Product deleted successfully"}
