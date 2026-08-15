from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from typing import List
from app.services import address_service
from app.schemas.address import Address, AddressCreate, AddressUpdate

from app.api import deps
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.models.order import Order
from app.services import dashboard_service, membership_service, order_service
from app.schemas.user import User as UserSchema, UserProfile, OrderInProfile
from app.schemas.dashboard import OrderStatus

router = APIRouter()

ORDER_STATUS_MAP = {
    OrderStatus.DIPROSES: ("Diproses", "processing"),
    OrderStatus.DIKIRIM: ("Dikirim", "shipped"),
    OrderStatus.SELESAI: ("Selesai", "completed"),
    OrderStatus.DIBATALKAN: ("Dibatalkan", "cancelled"),
}


def _build_profile_orders(user: User) -> List[OrderInProfile]:
    orders: List[OrderInProfile] = []
    sorted_orders = sorted(
        user.orders, key=lambda o: o.created_at or "", reverse=True
    )[:10]
    for order in sorted_orders:
        first_item = order.items[0] if order.items else None
        product = first_item.product if first_item else None
        status_label, status_code = ORDER_STATUS_MAP.get(
            order.status,
            (order.status.value if order.status else "", ""),
        )
        action = None
        if status_code == "shipped":
            action = "Lacak"
        elif status_code == "completed":
            action = "Beli Lagi"
        price = float(
            first_item.subtotal if first_item else (order.total_amount or 0)
        )
        orders.append(
            OrderInProfile(
                id=str(order.id),
                order_number=order.order_number,
                product={
                    "id": product.id if product else (first_item.product_id if first_item else None),
                    "name": product.name if product else (first_item.product_name if first_item else None),
                    "image": product.image if product else None,
                },
                price=price,
                status=status_label,
                status_code=status_code,
                action=action,
                created_at=order.created_at,
            )
        )
    return orders

class ProfileUpdate(BaseModel):
    name:  Optional[str]      = None
    email: Optional[EmailStr] = None
    photoprofil: Optional[str] = None

class PasswordUpdate(BaseModel):
    password_lama: str = Field(..., min_length=1)
    password_baru: str = Field(..., min_length=8)

@router.get("/dashboard")
def read_user_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_regular_user)
) -> Any:
    return dashboard_service.get_user_dashboard(db, current_user)

@router.get("/me", response_model=UserProfile)
def get_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    membership = membership_service.get_membership_view(db, current_user)
    orders = _build_profile_orders(current_user)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_admin": current_user.is_admin,
        "role_id": current_user.role_id,
        "member_type": current_user.member_type,
        "photoprofil": current_user.photoprofil,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "role": current_user.role,
        "membership": membership,
        "orders": orders,
    }

@router.put("/me", response_model=UserSchema)
def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if body.name:
        current_user.name = body.name
    if body.email:
        existing = db.query(User).filter(User.email == body.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah digunakan akun lain")
        current_user.email = body.email
    if "photoprofil" in body.model_fields_set:
        current_user.photoprofil = body.photoprofil
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
def update_password(
    body: PasswordUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if not verify_password(body.password_lama, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password lama salah")
    current_user.hashed_password = get_password_hash(body.password_baru)
    db.commit()
    return {"message": "Password berhasil diubah"}

@router.get("/me/addresses", response_model=List[Address])
def get_addresses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return address_service.get_user_addresses(db, user_id=current_user.id)


@router.post("/me/addresses", response_model=Address)
def create_address(
    body: AddressCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return address_service.create_address(db, user_id=current_user.id, data=body)


@router.put("/me/addresses/{id}", response_model=Address)
def update_address(
    id: str,
    body: AddressUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    address = address_service.update_address(db, address_id=id, user_id=current_user.id, data=body)
    if not address:
        raise HTTPException(status_code=404, detail="Alamat tidak ditemukan")
    return address


@router.delete("/me/addresses/{id}")
def delete_address(
    id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    ok = address_service.delete_address(db, address_id=id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alamat tidak ditemukan")
    return {"message": "Alamat berhasil dihapus"}
