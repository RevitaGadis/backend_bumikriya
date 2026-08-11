from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.cart import Cart, CartItemCreate, CartItemUpdate
from app.services import cart_service
from app.models.user import User

router = APIRouter()


@router.get("", response_model=Cart)
def read_cart(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve the current user's cart. A cart is created automatically if none exists.
    """
    cart = cart_service.get_or_create_cart(db, current_user.id)
    return cart


@router.post("/items", response_model=Cart)
def add_cart_item(
    item_in: CartItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Add a product to the current user's cart.
    """
    result = cart_service.add_item(
        db, user_id=current_user.id, product_id=item_in.product_id, quantity=item_in.quantity
    )
    if result == "out_of_stock":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity exceeds available stock",
        )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive",
        )
    return result


@router.put("/items/{item_id}", response_model=Cart)
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update the quantity of a cart item.
    """
    result = cart_service.update_item_quantity(
        db, user_id=current_user.id, item_id=item_id, quantity=item_in.quantity
    )
    if result == "out_of_stock":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity exceeds available stock",
        )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )
    return result


@router.delete("/items/{item_id}", response_model=Cart)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove an item from the current user's cart.
    """
    removed = cart_service.remove_item(db, user_id=current_user.id, item_id=item_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )
    return cart_service.get_cart(db, current_user.id)


@router.delete("", response_model=Cart)
def clear_cart(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove all items from the current user's cart.
    """
    cleared = cart_service.clear_cart(db, user_id=current_user.id)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )
    return cart_service.get_cart(db, current_user.id)
