from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import deps
from app.services import voucher_service
from app.schemas.voucher import Voucher, VoucherCreate, VoucherUpdate
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Voucher])
def read_vouchers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
) -> Any:
    vouchers = voucher_service.get_vouchers(db, skip=skip, limit=limit, is_active=is_active)
    return vouchers

@router.get("/{voucher_id}", response_model=Voucher)
def read_voucher(
    voucher_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    voucher = voucher_service.get_voucher(db, voucher_id=voucher_id)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher tidak ditemukan",
        )
    return voucher

@router.post("/", response_model=Voucher, status_code=status.HTTP_201_CREATED)
def create_voucher(
    *,
    db: Session = Depends(deps.get_db),
    voucher_in: VoucherCreate,
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    existing = voucher_service.get_voucher_by_code(db, code=voucher_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher dengan kode ini sudah ada.",
        )
    voucher = voucher_service.create_voucher(db, voucher=voucher_in, created_by=current_user.id)
    return voucher

def _require_manager(voucher: Any, current_user: User) -> None:
    is_admin = current_user.is_admin or (
        current_user.role and current_user.role.name == "admin"
    )
    if not is_admin and voucher.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin atau pembuat voucher yang dapat mengubah voucher ini.",
        )

@router.put("/{voucher_id}", response_model=Voucher)
def update_voucher(
    voucher_id: str,
    *,
    db: Session = Depends(deps.get_db),
    voucher_in: VoucherUpdate,
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    voucher = voucher_service.get_voucher(db, voucher_id=voucher_id)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher tidak ditemukan",
        )
    _require_manager(voucher, current_user)
    if voucher_in.code is not None and voucher_in.code != voucher.code:
        existing = voucher_service.get_voucher_by_code(db, code=voucher_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voucher dengan kode ini sudah ada.",
            )
    voucher = voucher_service.update_voucher(db, voucher_id=voucher_id, voucher=voucher_in)
    return voucher

@router.delete("/{voucher_id}")
def delete_voucher(
    voucher_id: str,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_seller)
) -> Any:
    voucher = voucher_service.get_voucher(db, voucher_id=voucher_id)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher tidak ditemukan",
        )
    _require_manager(voucher, current_user)
    try:
        voucher_service.delete_voucher(db, voucher_id=voucher_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher tidak dapat dihapus karena sedang digunakan oleh pesanan yang ada.",
        )
    return {"message": "Voucher berhasil dihapus"}