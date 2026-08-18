from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import deps
from app.services import category_service
from app.schemas.category import Category, CategoryCreate, CategoryUpdate
from app.core.uploads import save_upload
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Category])
def read_categories(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    categories = category_service.get_categories(db, skip=skip, limit=limit)
    return categories

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:

    existing = category_service.get_category_by_name(db, name=name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kategori dengan nama ini sudah ada.",
        )
    image_path = save_upload(image, subdir="categories") if image else None
    category_in = CategoryCreate(
        name=name,
        description=description,
        is_active=is_active,
        image=image_path,
    )
    category = category_service.create_category(db, category=category_in)
    return category

@router.get("/{category_id}", response_model=Category)
def read_category(
    category_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori tidak ditemukan",
        )
    return category

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: str,
    *,
    db: Session = Depends(deps.get_db),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_admin: User = Depends(deps.get_current_admin)
) -> Any:
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori tidak ditemukan",
        )
    if name and name != category.name:
        existing = category_service.get_category_by_name(db, name=name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kategori dengan nama ini sudah ada.",
            )
    image_path = save_upload(image, subdir="categories") if image else None
    category_in = CategoryUpdate(
        name=name,
        description=description,
        is_active=is_active,
        image=image_path,
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
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori tidak ditemukan",
        )
    try:
        category_service.delete_category(db, category_id=category_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kategori tidak dapat dihapus karena masih digunakan oleh produk yang ada.",
        )
    return {"message": "Kategori berhasil dihapus"}