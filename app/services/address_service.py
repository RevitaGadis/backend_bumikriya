from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


def get_user_addresses(db: Session, user_id: str) -> List[Address]:
    return (
        db.query(Address)
        .filter(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
        .all()
    )


def get_address(db: Session, address_id: str, user_id: str) -> Optional[Address]:
    return (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user_id)
        .first()
    )


def _unset_other_defaults(db: Session, user_id: str, exclude_id: Optional[str] = None) -> None:
    query = db.query(Address).filter(Address.user_id == user_id, Address.is_default == True)  # noqa: E712
    if exclude_id:
        query = query.filter(Address.id != exclude_id)
    query.update({Address.is_default: False})


def create_address(db: Session, user_id: str, data: AddressCreate) -> Address:
    if data.is_default:
        _unset_other_defaults(db, user_id)

    address = Address(user_id=user_id, **data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, address_id: str, user_id: str, data: AddressUpdate) -> Optional[Address]:
    address = get_address(db, address_id=address_id, user_id=user_id)
    if not address:
        return None

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_default") is True:
        _unset_other_defaults(db, user_id, exclude_id=address_id)

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address_id: str, user_id: str) -> bool:
    address = get_address(db, address_id=address_id, user_id=user_id)
    if not address:
        return False
    db.delete(address)
    db.commit()
    return True