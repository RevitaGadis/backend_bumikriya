from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.order import Order, OrderDetailResponse, OrderUpdate
from app.services import order_service
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Order])
def read_orders(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    current_user: User = Depends(deps.get_current_admin_or_seller),
) -> Any:
    """
    Retrieve orders with their items and payment. (Admin or seller only)
    Optional `user_id` query param to filter by customer.
    """
    return order_service.get_orders(db, skip=skip, limit=limit, user_id=user_id)


@router.get("/me", response_model=List[Order])
def read_my_orders(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """List order milik user yang sedang login. (Buyer)"""
    return order_service.get_orders(db, skip=skip, limit=limit, user_id=current_user.id)


@router.get("/me/{order_id}", response_model=Order)
def read_my_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Detail order milik sendiri. (Buyer)"""
    order = order_service.get_order(db, order_id=order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/{order_id}", response_model=Order)
def read_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_seller),
) -> Any:
    """
    Retrieve a single order detail including items and payment. (Admin or seller only)
    """
    order = order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.get("/{order_id}/detail", response_model=OrderDetailResponse)
def read_order_detail(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_seller),
) -> Any:
    """
    Retrieve a full order detail including status, customer, items, payment,
    shipping and status history. (Admin or seller only)
    """
    order_detail = order_service.get_order_detail(db, order_id=order_id)
    if not order_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return {"success": True, "data": order_detail}


@router.put("/{order_id}", response_model=Order)
def update_order(
    order_id: int,
    order_in: OrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_seller),
) -> Any:
    """
    Update an order (e.g. status or shipping address). (Admin or seller only)
    """
    order = order_service.update_order(db, order_id=order_id, order=order_in)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order
