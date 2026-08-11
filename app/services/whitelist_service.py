from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.whitelist import Whitelist


def get_user_whitelists(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
) -> List[Whitelist]:
    return (
        db.query(Whitelist)
        .filter(Whitelist.user_id == user_id)
        .order_by(Whitelist.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_whitelist_item(
    db: Session, user_id: str, product_id: str
) -> Optional[Whitelist]:
    return (
        db.query(Whitelist)
        .filter(Whitelist.user_id == user_id, Whitelist.product_id == product_id)
        .first()
    )


def add_to_whitelist(db: Session, user_id: str, product_id: str) -> Optional[Whitelist]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    existing = get_user_whitelist_item(db, user_id=user_id, product_id=product_id)
    if existing:
        return existing

    item = Whitelist(user_id=user_id, product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_whitelist(db: Session, user_id: str, item_id: int) -> bool:
    item = (
        db.query(Whitelist)
        .filter(Whitelist.id == item_id, Whitelist.user_id == user_id)
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
