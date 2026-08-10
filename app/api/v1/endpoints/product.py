from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services import product_service
from app.schemas.product import Product, ProductCreate, ProductUpdate
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
    product_id: int,
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
    product_in: ProductCreate,
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    """
    Create a new product. (Admin or seller only)
    """
    product = product_service.get_product_by_name(db, name=product_in.name)
    if product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this name already exists.",
        )
    product = product_service.create_product(db, product=product_in)
    return product

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductUpdate,
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    """
    Update a product. (Admin or seller only)
    """
    product = product_service.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    product = product_service.update_product(db, product_id=product_id, product=product_in)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
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
