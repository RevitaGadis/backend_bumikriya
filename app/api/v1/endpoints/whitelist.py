from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.whitelist import Whitelist, WhitelistCreate
from app.services import whitelist_service

router = APIRouter()


@router.get("/", response_model=List[Whitelist])
def read_whitelists(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return whitelist_service.get_user_whitelists(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=Whitelist)
def add_to_whitelist(
    body: WhitelistCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    item = whitelist_service.add_to_whitelist(
        db=db,
        user_id=current_user.id,
        product_id=body.product_id,
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return item


@router.delete("/{item_id}")
def remove_from_whitelist(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    removed = whitelist_service.remove_from_whitelist(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelist item not found",
        )
    return {"message": "Whitelist item removed"}
