from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.services import product_service
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductDetail
from app.core.uploads import save_upload
from app.models.user import User
from app.models.store import Store
from app.services import review_service


router = APIRouter()

@router.get("/", response_model=List[Product])
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve products. (Public)
    """
    products = product_service.get_products(db, skip=skip, limit=limit)
    return products

@router.get("/{product_id}", response_model=ProductDetail)
def read_product(
    product_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Retrieve a single product with full detail (public).
    """
    product = product_service.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    images = [
        {
            "id": f"img_{product.id}",
            "url": product.image,
            "is_primary": True,
        }
    ]

    specifications = []
    if product.material:
        specifications.append({"name": "Material", "value": product.material})
    if product.color:
        specifications.append({"name": "Color", "value": product.color})
    if product.fits:
        specifications.append({"name": "Fits", "value": product.fits})

    badges = [b for b in [product.material] if b]

    category = None
    if product.category:
        category = {"id": product.category.id, "name": product.category.name}

    seller = None
    if product.seller:
        store = db.query(Store).filter(Store.user_id == product.seller.id).first()
        seller = {
            "id": product.seller.id,
            "store_id": store.id if store else None,
            "store_name": store.store_name if store else None,
            "name": (store.store_name if store else None) or product.seller.name,
            "avatar_url": store.logo if store else product.seller.photoprofil,
            "badge": None,
            "location": product.seller.address,
        }

    related = product_service.get_related_products(db, product=product, limit=3)
    related_products = [
        {
            "id": rp.id,
            "name": rp.name,
            "price": rp.price,
            "currency": "USD",
            "image_url": rp.image,
        }
        for rp in related
    ]

    return {
        "id": product.id,
        "name": product.name,
        "description": None,
        "price": product.price,
        "currency": "USD",
        "stock": product.stock,
        "images": images,
        "badges": badges,
        "category": category,
        "specifications": specifications,
        "care_instructions": [],
        "shipping_info": {
            "processing_time": "2-4 business days",
            "shipping_method": "Standard Shipping",
            "estimated_delivery": "5-8 business days",
        },
        "seller": seller,
        "related_products": related_products,
        "created_at": None,
        "updated_at": None,
    }

@router.post("/", response_model=Product)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    color: str = Form(...),
    material: str = Form(...),
    fits: str = Form(...),
    stock: int = Form(0),
    category_id: str = Form(...),
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
    product_in = ProductCreate(
        name=name,
        price=price,
        description=description,
        image=image_path,
        color=color,
        material=material,
        fits=fits,
        stock=stock,
        category_id=category_id,
        is_active=is_active,
    )
    product = product_service.create_product(db, product_in, seller_id=current_user.id)
    return product

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: str,
    *,
    db: Session = Depends(deps.get_db),
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
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
    if description is not None:
        data["description"] = description
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
