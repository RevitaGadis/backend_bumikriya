from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.wishlist import Wishlist


def get_user_wishlists(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
) -> List[Wishlist]:
    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id)
        .order_by(Wishlist.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_wishlist_item(
    db: Session, user_id: str, product_id: str
) -> Optional[Wishlist]:
    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
        .first()
    )


def add_to_wishlist(db: Session, user_id: str, product_id: str) -> Optional[Wishlist]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    existing = get_user_wishlist_item(db, user_id=user_id, product_id=product_id)
    if existing:
        return existing

    item = Wishlist(user_id=user_id, product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist(db: Session, user_id: str, item_id: int) -> bool:
    item = (
        db.query(Wishlist)
        .filter(Wishlist.id == item_id, Wishlist.user_id == user_id)
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
