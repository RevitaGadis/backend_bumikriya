from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.order import Order
from app.schemas.checkout import CheckoutRequest
from app.services import checkout_service
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=Order, status_code=201)
def checkout(
    *,
    db: Session = Depends(deps.get_db),
    checkout_in: CheckoutRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return checkout_service.checkout(db, current_user.id, checkout_in)