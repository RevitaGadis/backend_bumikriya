from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.wishlist import Wishlist, WishlistCreate
from app.services import wishlist_service

router = APIRouter()


@router.get("/", response_model=List[Wishlist])
def read_wishlists(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return wishlist_service.get_user_wishlists(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=Wishlist)
def add_to_wishlist(
    body: WishlistCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    item = wishlist_service.add_to_wishlist(
        db=db,
        user_id=current_user.id,
        product_id=body.product_id,
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan",
        )
    return item


@router.delete("/{item_id}")
def remove_from_wishlist(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    removed = wishlist_service.remove_from_wishlist(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item di wishlist tidak ditemukan",
        )
    return {"message": "Item di wishlist dihapus"}
