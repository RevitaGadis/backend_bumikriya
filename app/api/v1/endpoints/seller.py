from typing import Any
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services import dashboard_service
from app.schemas.seller import SellerMeResponse

router = APIRouter()


def _store_name(user: User) -> str:
    return user.store_name or user.name


def _store_slug(user: User) -> str:
    if user.store_slug:
        return user.store_slug
    slug = re.sub(r"[^a-z0-9]+", "-", _store_name(user).lower()).strip("-")
    return slug or user.id


@router.get("/dashboard")
def read_seller_dashboard(
    db: Session = Depends(deps.get_db),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    return dashboard_service.get_user_dashboard(db, current_seller)


@router.get("/me", response_model=SellerMeResponse)
def read_seller_me(
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    return {
        "success": True,
        "message": "Seller ditemukan",
        "data": {
            "user": {
                "id": current_seller.id,
                "name": current_seller.name,
                "email": current_seller.email,
                "role": "seller",
            },
            "seller": {
                "id": current_seller.id,
                "store_name": _store_name(current_seller),
                "store_slug": _store_slug(current_seller),
                "status": current_seller.status,
            },
        },
    }
