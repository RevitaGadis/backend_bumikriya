from typing import List, Optional, Tuple
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.store import Store
from app.models.store_follow import StoreFollow
from app.models.user import User
from app.models.role import Role
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.wishlist import Wishlist
from app.schemas.store import StoreUpdate
from app.schemas.dashboard import OrderStatus


def get_store_by_user(db: Session, user_id: str) -> Optional[Store]:
    return db.query(Store).filter(Store.user_id == user_id).first()


def get_store_by_id(db: Session, store_id: str) -> Optional[Store]:
    return db.query(Store).filter(Store.id == store_id).first()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "store"


def is_user_following(db: Session, user_id: Optional[str], store_id: str) -> bool:
    if not user_id:
        return False
    return (
        db.query(StoreFollow)
        .filter(StoreFollow.store_id == store_id, StoreFollow.user_id == user_id)
        .first()
        is not None
    )


def follow_store(db: Session, user_id: str, store_id: str) -> bool:
    """Follow toko. Return True kalau berhasil / sudah follow, False kalau toko tidak ada."""
    store = get_store_by_id(db, store_id)
    if not store:
        return False

    existing = (
        db.query(StoreFollow)
        .filter(StoreFollow.store_id == store_id, StoreFollow.user_id == user_id)
        .first()
    )
    if not existing:
        db.add(StoreFollow(store_id=store_id, user_id=user_id))
        db.commit()
    return True


def unfollow_store(db: Session, user_id: str, store_id: str) -> bool:
    """Unfollow toko. Return True kalau berhasil, False kalau toko tidak ada."""
    store = get_store_by_id(db, store_id)
    if not store:
        return False

    existing = (
        db.query(StoreFollow)
        .filter(StoreFollow.store_id == store_id, StoreFollow.user_id == user_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
    return True


def _format_sales_count(count: int) -> str:
    if count >= 1000:
        value = count / 1000.0
        text = f"{value:.1f}k".rstrip("0").rstrip(".")
        return f"{text}k+"
    return str(count)


def _total_sold(db: Session, seller_id: str) -> int:
    return (
        db.query(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != OrderStatus.DIBATALKAN)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Product.seller_id == seller_id)
        .scalar()
        or 0
    )


def build_store_detail(db: Session, store: Store, current_user: Optional[User]) -> dict:
    seller = store.user
    total_products = (
        db.query(Product)
        .filter(Product.seller_id == store.user_id, Product.is_active.is_(True))
        .count()
    )
    total_sales = _total_sold(db, store.user_id)
    active_since = store.created_at.year if store.created_at else None
    is_following = is_user_following(db, current_user.id if current_user else None, store.id)

    return {
        "id": store.id,
        "name": store.store_name,
        "slug": slugify(store.store_name),
        "seller": {
            "id": seller.id if seller else store.user_id,
            "name": seller.name if seller else store.store_name,
            "avatar_url": seller.photoprofil if seller else None,
        },
        "profile": {
            "avatar_url": store.logo,
            "banner_url": None,
            "badge": None,
            "location": {
                "city": None,
                "state": None,
                "country": None,
                "display_name": store.address,
            },
        },
        "statistics": {
            "rating": None,
            "total_reviews": 0,
            "total_sales": int(total_sales),
            "sales_display": _format_sales_count(int(total_sales)),
            "active_since": active_since,
            "total_products": total_products,
        },
        "about": {
            "title": "Our Story",
            "description": store.description,
            "tags": [],
        },
        "shop_rules": {
            "shipping": None,
            "returns": None,
            "commissions": None,
        },
        "is_following": is_following,
        "created_at": store.created_at,
        "updated_at": None,
    }


def get_store_products(
    db: Session,
    store_id: str,
    user_id: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[dict], int]:
    """Produk toko (active saja) dengan pagination. Return (items, total)."""
    store = get_store_by_id(db, store_id)
    if not store:
        return [], 0

    query = db.query(Product).filter(
        Product.seller_id == store.user_id,
        Product.is_active.is_(True),
    )
    total = query.count()
    products = (
        query.order_by(Product.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    favorited_ids = set()
    if user_id:
        favorited_ids = {
            row[0]
            for row in db.query(Wishlist.product_id)
            .filter(Wishlist.user_id == user_id)
            .all()
        }

    items = [
        {
            "id": p.id,
            "name": p.name,
            "slug": slugify(p.name),
            "price": p.price,
            "currency": "USD",
            "thumbnail_url": p.image,
            "rating": None,
            "total_reviews": 0,
            "is_favorite": p.id in favorited_ids,
        }
        for p in products
    ]

    return items, total


def register_seller(
    db: Session,
    current_user: User,
    store_name: str,
    description: Optional[str] = None,
    logo: Optional[str] = None,
    address: Optional[str] = None,
) -> Store:
    existing = get_store_by_user(db, current_user.id)
    if existing:
        return existing

    seller_role = db.query(Role).filter(Role.name == "seller").first()
    if seller_role:
        current_user.role_id = seller_role.id
        db.add(current_user)

    db_store = Store(
        user_id=current_user.id,
        store_name=store_name,
        description=description,
        logo=logo,
        address=address,
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store


def update_store(db: Session, user_id: str, store_in: StoreUpdate) -> Optional[Store]:
    db_store = get_store_by_user(db, user_id)
    if not db_store:
        return None
    update_data = store_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_store, key, value)
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store