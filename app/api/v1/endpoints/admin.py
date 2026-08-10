from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services import dashboard_service
from app.schemas.dashboard import AdminDashboard
from app.schemas.user import User as UserSchema
from app.schemas.transaction import Transaction as TransactionSchema
from app.models.transaction import Transaction

router = APIRouter()

@router.get("/dashboard", response_model=AdminDashboard)
def read_admin_dashboard(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    return dashboard_service.get_admin_dashboard(db)

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
