from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.uploads import save_upload

from app.api import deps
from app.models.user import User
from app.services import dashboard_service, customer_service
from app.schemas.dashboard import AdminDashboard
from app.schemas.user import User as UserSchema
from app.schemas.customer import (
    CustomerListResponse,
    CustomerDetailResponse,
    CustomerUpdate,
    CustomerUpdateResponse,
    CustomerOrderHistoryResponse,
    AdminOrderDetailResponse,
)
from app.schemas.transaction import Transaction as TransactionSchema
from app.models.transaction import Transaction

router = APIRouter()

@router.get("/dashboard", response_model=AdminDashboard)
def read_admin_dashboard(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    return dashboard_service.get_admin_dashboard(db)

@router.get("/customers", response_model=CustomerListResponse)
def read_customers(
    db: Session = Depends(deps.get_db),
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve customers list with statistics, top customer and pagination. (Admin only)
    """
    data = customer_service.get_customers(
        db, page=page, limit=limit, search=search
    )
    return {"success": True, "data": data}

@router.get("/users", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    """
    Retrieve users. (Admin only)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/transactions", response_model=List[TransactionSchema])
def read_all_transactions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    """
    Retrieve all transactions in the system. (Admin only)
    """
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
    return transactions

@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def read_customer_detail(
    customer_id: str,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve customer details/profile by customer_id. (Admin only)
    """
    detail = customer_service.get_customer_detail(db, customer_id=customer_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detail pelanggan tidak ditemukan",
        )
    return {
        "success": True,
        "message": "Detail pelanggan berhasil diambil",
        "data": detail
    }

@router.put("/customers/{customer_id}", response_model=CustomerUpdateResponse)
async def update_customer_data(
    customer_id: str,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Update customer details/profile by customer_id. (Admin only)
    """
    content_type = request.headers.get("content-type", "")
    data = {}
    if "multipart/form-data" in content_type:
        form_data = await request.form()
        name = form_data.get("name")
        email = form_data.get("email")
        phone = form_data.get("phone")
        address = form_data.get("address")
        member_type = form_data.get("member_type")
        avatar = form_data.get("avatar")
        
        if name:
            data["name"] = str(name)
        if email:
            data["email"] = str(email)
        if phone is not None:
            data["phone"] = str(phone)
        if address is not None:
            data["address"] = str(address)
        if member_type is not None:
            data["member_type"] = str(member_type)
            
        if avatar and hasattr(avatar, "filename") and avatar.filename:
            avatar_path = save_upload(avatar, subdir="customers")
            data["photoprofil"] = avatar_path
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        name = body.get("name")
        email = body.get("email")
        phone = body.get("phone")
        address = body.get("address")
        member_type = body.get("member_type")
        
        if name:
            data["name"] = name
        if email:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if address is not None:
            data["address"] = address
        if member_type is not None:
            data["member_type"] = member_type

    if not data.get("name") or not data.get("email"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name and email are required fields",
        )

    updated = customer_service.update_customer(
        db, customer_id=customer_id, data=data
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detail pelanggan tidak ditemukan",
        )
    return {
        "success": True,
        "message": "Data pelanggan berhasil diperbarui",
        "data": updated
    }

@router.get("/customers/{customer_id}/orders", response_model=CustomerOrderHistoryResponse)
def read_customer_order_history(
    customer_id: str,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve customer order history. (Admin only)
    """
    customer = db.query(User).filter(User.id == customer_id, User.role.has(name="user")).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detail pelanggan tidak ditemukan",
        )
    
    result = customer_service.get_customer_orders(
        db, customer_id=customer_id, page=page, limit=limit
    )
    return {
        "success": True,
        "message": "Riwayat pesanan berhasil diambil",
        "data": result["orders"],
        "pagination": result["pagination"]
    }

@router.get("/orders/{order_id}", response_model=AdminOrderDetailResponse)
def read_admin_order_detail(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve order details for admin. (Admin only)
    """
    order_detail = customer_service.get_admin_order_detail(db, order_id=order_id)
    if not order_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesanan tidak ditemukan",
        )
    return {
        "success": True,
        "data": order_detail
    }
