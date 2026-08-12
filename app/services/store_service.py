from typing import Optional
from sqlalchemy.orm import Session
from app.models.store import Store
from app.models.user import User
from app.models.role import Role
from app.schemas.store import StoreCreate, StoreUpdate


def get_store_by_user(db: Session, user_id: str) -> Optional[Store]:
    return db.query(Store).filter(Store.user_id == user_id).first()


def register_seller(db: Session, current_user: User, store_in: StoreCreate) -> Store:
    existing = get_store_by_user(db, current_user.id)
    if existing:
        return existing

    seller_role = db.query(Role).filter(Role.name == "seller").first()
    if seller_role:
        current_user.role_id = seller_role.id
        db.add(current_user)

    db_store = Store(
        user_id=current_user.id,
        store_name=store_in.store_name,
        description=store_in.description,
        logo=store_in.logo,
        address=store_in.address,
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