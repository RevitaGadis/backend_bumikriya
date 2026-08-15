from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.services import payment_service
from app.models.user import User

router = APIRouter()


@router.post("/webhook")
async def payment_webhook(
    payload: dict,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Dipanggil OTOMATIS oleh Midtrans, bukan oleh user. (Public, no auth)"""
    return payment_service.handle_webhook(db, payload)

@router.post("/{order_id}")
def create_payment(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Generate Snap token buat bayar order tertentu. (Buyer)"""
    return payment_service.create_snap_transaction(db, order_id, current_user.id)