from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services import category_service
from app.schemas.category import Category, CategoryCreate, CategoryUpdate
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Category])
def read_categories(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve categories.
    """
    categories = category_service.get_categories(db, skip=skip, limit=limit)
    return categories