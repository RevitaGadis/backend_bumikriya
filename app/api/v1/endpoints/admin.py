from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.uploads import save_upload

from app.api import deps
from app.models.user import User
from app.services import account_service, dashboard_service, customer_service, user_service
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
from app.schemas.account import (
    AdminAccountListResponse,
    AdminAccountSummaryResponse,
    AdminAccountDetailResponse,
    AdminAccountCreateResponse,
    AdminAccountUpdateResponse,
    AdminAccountStatusUpdate,
)

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

@router.get("/accounts/summary", response_model=AdminAccountSummaryResponse)
def read_accounts_summary(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve account statistics (total, verified, role & status distribution). (Admin only)
    """
    return {
        "success": True,
        "data": account_service.get_account_summary(db)
    }

@router.get("/accounts", response_model=AdminAccountListResponse)
def read_accounts(
    db: Session = Depends(deps.get_db),
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve accounts list (admin & seller) with pagination. (Admin only)
    """
    data = account_service.get_accounts(
        db, page=page, limit=limit, search=search
    )
    return {
        "success": True,
        "message": "Accounts retrieved successfully",
        "data": data,
    }

@router.get("/accounts/{account_id}", response_model=AdminAccountDetailResponse)
def read_account_detail(
    account_id: str,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve account detail by account_id. (Admin only)
    """
    account = account_service.get_account_detail(db, account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return {
        "success": True,
        "message": "Account retrieved successfully",
        "data": account,
    }

@router.post("/accounts", response_model=AdminAccountCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("seller"),
    avatar: Optional[UploadFile] = File(None),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Create a new account with optional avatar. (Admin only)
    """
    if len(password) < 8 or len(password) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password harus antara 8 dan 72 karakter",
        )
    if user_service.get_user_by_email(db, email=email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah digunakan",
        )

    photoprofil = None
    if avatar and avatar.filename:
        photoprofil = save_upload(avatar, subdir="avatars")

    account = account_service.create_account(
        db,
        {
            "name": name,
            "email": email,
            "password": password,
            "role": role,
            "photoprofil": photoprofil,
        },
    )
    return {
        "success": True,
        "message": "Account created successfully",
        "data": account,
    }

@router.patch("/accounts/{account_id}", response_model=AdminAccountUpdateResponse)
async def update_account(
    account_id: str,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    status_: Optional[str] = Form(None, alias="status"),
    avatar: Optional[UploadFile] = File(None),
    remove_avatar: Optional[bool] = Form(None),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Update account data with optional avatar change/removal. (Admin only)
    """
    data = {}
    if name is not None:
        data["name"] = name
    if email is not None:
        data["email"] = email
    if role is not None:
        data["role"] = role
    if status_ is not None:
        data["status"] = status_
    if remove_avatar is not None:
        data["remove_avatar"] = remove_avatar
    if avatar and avatar.filename:
        data["photoprofil"] = save_upload(avatar, subdir="avatars")

    try:
        account = account_service.update_account(db, account_id=account_id, data=data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return {
        "success": True,
        "message": "Account updated successfully",
        "data": account,
    }

@router.patch("/accounts/{account_id}/status", response_model=AdminAccountUpdateResponse)
def update_account_status(
    account_id: str,
    body: AdminAccountStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Activate / deactivate an account. (Admin only)
    """
    try:
        account = account_service.update_account_status(
            db, account_id=account_id, status_value=body.status
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return {
        "success": True,
        "message": "Account updated successfully",
        "data": account,
    }
