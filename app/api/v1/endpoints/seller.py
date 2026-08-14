from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.services import product_service, order_service, store_service, voucher_service
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductStockUpdate
from app.schemas.order import OrderStatusUpdate
from app.schemas.store import Store, StoreUpdate
from app.schemas.voucher import Voucher
from app.core.uploads import save_upload
from app.models.user import User

router = APIRouter()


# ---------- Register jadi seller ----------

@router.post("/register", response_model=Store, status_code=status.HTTP_201_CREATED)
def register_as_seller(
    *,
    db: Session = Depends(deps.get_db),
    store_name: str = Form(...),
    description: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Upgrade akun jadi seller + bikin toko. (User biasa yang login)"""
    logo_path = None
    if logo and logo.filename:
        logo_path = save_upload(logo, subdir="stores")
    return store_service.register_seller(
        db, current_user, store_name, description=description, logo=logo_path, address=address
    )


@router.get("/store", response_model=Store)
def read_my_store(
    db: Session = Depends(deps.get_db),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Lihat data toko sendiri. (Seller only)"""
    store = store_service.get_store_by_user(db, current_seller.id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.put("/store", response_model=Store)
def update_my_store(
    *,
    db: Session = Depends(deps.get_db),
    store_in: StoreUpdate,
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Update data toko sendiri. (Seller only)"""
    store = store_service.update_store(db, current_seller.id, store_in)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


# ---------- Produk ----------

@router.get("/products", response_model=List[Product])
def read_seller_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """List produk milik seller yang login. (Seller only)"""
    return product_service.get_products_by_seller(db, current_seller.id, skip, limit)


@router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_seller_product(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Form(...),
    price: float = Form(...),
    color: str = Form(...),
    material: str = Form(...),
    fits: str = Form(...),
    stock: int = Form(0),
    category_id: str = Form(...),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Tambah produk baru. (Seller only)"""
    image_path = save_upload(image) if image else "/images/products/default.jpg"
    product_in = ProductCreate(
        name=name,
        price=price,
        image=image_path,
        color=color,
        material=material,
        fits=fits,
        stock=stock,
        category_id=category_id,
        is_active=is_active,
    )
    return product_service.create_product(db, product_in, seller_id=current_seller.id)


@router.put("/products/{product_id}", response_model=Product)
async def update_seller_product(
    product_id: str,
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    color: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    fits: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    category_id: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Update produk milik sendiri. (Seller only)"""
    update_data: dict = {}
    if name is not None:
        update_data["name"] = name
    if price is not None:
        update_data["price"] = price
    if color is not None:
        update_data["color"] = color
    if material is not None:
        update_data["material"] = material
    if fits is not None:
        update_data["fits"] = fits
    if stock is not None:
        update_data["stock"] = stock
    if category_id is not None:
        update_data["category_id"] = category_id
    if is_active is not None:
        update_data["is_active"] = is_active

    image_field = (await request.form()).get("image")
    if image_field is not None:
        if isinstance(image_field, str) and image_field.strip():
            update_data["image"] = image_field.strip()
        elif hasattr(image_field, "filename") and image_field.filename:
            update_data["image"] = save_upload(image_field)

    product_in = ProductUpdate(**update_data)
    product = product_service.update_seller_product(db, product_id, current_seller.id, product_in)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
    return product


@router.delete("/products/{product_id}")
def delete_seller_product(
    product_id: str,
    *,
    db: Session = Depends(deps.get_db),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Hapus produk milik sendiri. (Seller only)"""
    deleted = product_service.delete_seller_product(db, product_id, current_seller.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
    return {"message": "Product deleted successfully"}


@router.put("/products/{product_id}/stock", response_model=Product)
def update_seller_product_stock(
    product_id: str,
    *,
    db: Session = Depends(deps.get_db),
    stock_in: ProductStockUpdate,
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Update stok produk milik sendiri. (Seller only)"""
    product = product_service.update_seller_product_stock(db, product_id, current_seller.id, stock_in.stock)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
    return product


# ---------- Orders ----------

@router.get("/orders")
def read_seller_orders(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """List order yang mengandung produk milik seller ini. (Seller only)"""
    return order_service.get_orders_for_seller(db, current_seller.id, skip, limit)


@router.put("/orders/{order_id}/status")
def update_seller_order_status(
    order_id: int,
    *,
    db: Session = Depends(deps.get_db),
    status_in: OrderStatusUpdate,
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Update status order (hanya yang ada produk milik seller ini). (Seller only)"""
    order = order_service.update_seller_order_status(db, order_id, current_seller.id, status_in.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or does not contain your products")
    return order


# ---------- Vouchers ----------

@router.get("/vouchers", response_model=List[Voucher])
def read_seller_vouchers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """List voucher yang dibuat oleh seller yang login. (Seller only)"""
    return voucher_service.get_vouchers_by_creator(
        db, current_seller.id, skip, limit, is_active
    )


# ---------- Dashboard ----------

@router.get("/dashboard/summary")
def seller_dashboard_summary(
    db: Session = Depends(deps.get_db),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    """Ringkasan performa toko. (Seller only)"""
    return order_service.get_seller_dashboard_summary(db, current_seller.id)