from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.store import (
    StoreDetail,
    StoreProductListResponse,
    StoreProductItem,
    StorePagination,
    StoreReviewListResponse,
)
from app.services import store_service

router = APIRouter()


def _get_store_or_404(db: Session, store_id: str) -> Any:
    store = store_service.get_store_by_id_or_user(db, store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )
    return store


@router.get("/{store_id}", response_model=StoreDetail)
def read_store_detail(
    store_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
) -> Any:
    """Detail toko. Public, is_following otomatis false kalau belum login."""
    store = _get_store_or_404(db, store_id)
    return store_service.build_store_detail(db, store, current_user)


@router.get("/{store_id}/products", response_model=StoreProductListResponse)
def read_store_products(
    store_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
) -> Any:
    """Produk toko (active) dengan pagination. Public."""
    store = _get_store_or_404(db, store_id)
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    user_id = current_user.id if current_user else None

    items, total = store_service.get_store_products(
        db, store.id, user_id=user_id, page=page, limit=limit
    )

    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


@router.get("/{store_id}/reviews", response_model=StoreReviewListResponse)
def read_store_reviews(
    store_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Review toko. Public. (Belum ada tabel review, response kosong.)"""
    _get_store_or_404(db, store_id)
    page = max(page, 1)
    limit = min(max(limit, 1), 100)

    return {
        "data": [],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": 0,
            "total_pages": 0,
        },
    }


@router.post("/{store_id}/follow")
def follow_store(
    store_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Follow toko. (Login required)"""
    ok = store_service.follow_store(db, current_user.id, store_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )
    return {"message": "Store followed", "is_following": True}


@router.delete("/{store_id}/follow")
def unfollow_store(
    store_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Unfollow toko. (Login required)"""
    ok = store_service.unfollow_store(db, current_user.id, store_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )
    return {"message": "Store unfollowed", "is_following": False}