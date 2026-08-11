from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
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

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryCreate,
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    """
    Create a new category. (Admin only)
    """
    existing = category_service.get_category_by_name(db, name=category_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists.",
        )
    category = category_service.create_category(db, category=category_in)
    return category

@router.get("/{category_id}", response_model=Category)
def read_category(
    category_id: str,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    """
    Retrieve a single category. (Admin only)
    """
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: str,
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryUpdate,
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    """
    Update a category. (Admin only)
    """
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if category_in.name and category_in.name != category.name:
        existing = category_service.get_category_by_name(db, name=category_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category with this name already exists.",
            )
    category = category_service.update_category(db, category_id=category_id, category=category_in)
    return category

@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    *,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    """
    Delete a category. (Admin only)
    """
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    try:
        category_service.delete_category(db, category_id=category_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be deleted because it is used by existing transactions.",
        )
    return {"message": "Category deleted successfully"}