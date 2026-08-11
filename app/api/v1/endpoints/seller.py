from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services import dashboard_service

router = APIRouter()


@router.get("/dashboard")
def read_seller_dashboard(
    db: Session = Depends(deps.get_db),
    current_seller: User = Depends(deps.get_current_seller),
) -> Any:
    return dashboard_service.get_user_dashboard(db, current_seller)
