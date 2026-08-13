from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.membership import (
    MembershipType,
    UserMembership,
    MembershipBenefit,
)


def format_rupiah(amount: float) -> str:
    return "Rp {:,}".format(int(round(amount))).replace(",", ".")


def get_membership_types(db: Session) -> List[MembershipType]:
    return (
        db.query(MembershipType)
        .order_by(MembershipType.min_spending.asc())
        .all()
    )


def get_membership_type_by_code(db: Session, code: str) -> Optional[MembershipType]:
    return db.query(MembershipType).filter(MembershipType.code == code).first()


def get_or_create_default_membership_type(db: Session) -> Optional[MembershipType]:
    default_type = (
        db.query(MembershipType)
        .order_by(MembershipType.min_spending.asc())
        .first()
    )
    if default_type:
        return default_type

    default_type = MembershipType(
        name="Basic",
        code="basic",
        min_spending=0,
        discount_percentage=0,
        description="Default membership level",
    )
    db.add(default_type)
    db.commit()
    db.refresh(default_type)
    return default_type


def ensure_user_membership(db: Session, user) -> UserMembership:
    um = (
        db.query(UserMembership)
        .filter(UserMembership.user_id == user.id)
        .first()
    )
    if um:
        return um

    default_type = get_or_create_default_membership_type(db)
    um = UserMembership(
        user_id=user.id,
        membership_type_id=default_type.id if default_type else None,
        total_spending=0,
    )
    db.add(um)
    db.commit()
    db.refresh(um)
    return um


def _resolve_current_level(types: List[MembershipType], spending: float) -> Optional[MembershipType]:
    current = None
    for t in types:
        if spending >= t.min_spending:
            current = t
        else:
            break
    if current is None:
        current = types[0] if types else None
    return current


def recalc_user_membership(db: Session, user) -> UserMembership:
    um = ensure_user_membership(db, user)
    types = get_membership_types(db)
    spending = float(um.total_spending or 0)
    current = _resolve_current_level(types, spending)
    if current is not None:
        um.membership_type_id = current.id
    db.commit()
    db.refresh(um)
    return um


def add_spending(db: Session, user_id: str, amount: float) -> UserMembership:
    um = (
        db.query(UserMembership)
        .filter(UserMembership.user_id == user_id)
        .first()
    )
    if um is None:
        return None
    um.total_spending = float(um.total_spending or 0) + float(amount)
    db.commit()
    db.refresh(um)
    return recalc_user_membership(db, um.user)


def get_membership_view(db: Session, user) -> Optional[dict]:
    um = ensure_user_membership(db, user)
    types = get_membership_types(db)
    if not types:
        return None

    spending = float(um.total_spending or 0)
    current = _resolve_current_level(types, spending)
    if current is None:
        return None

    next_type = None
    for t in types:
        if t.min_spending > current.min_spending:
            next_type = t
            break

    if next_type is not None:
        span = next_type.min_spending - current.min_spending
        if span > 0:
            progress = (spending - current.min_spending) / span * 100
        else:
            progress = 100
        progress = max(0, min(100, round(progress)))
        remaining = max(0, next_type.min_spending - spending)
        progress_text = "Belanja {} lagi untuk menjadi {}".format(
            format_rupiah(remaining), next_type.name
        )
    else:
        progress = 100
        remaining = 0
        progress_text = "Anda telah mencapai level tertinggi {}".format(current.name)

    benefits = [b.benefit for b in current.benefits]

    return {
        "current_level": current.name,
        "current_level_code": current.code,
        "next_level": next_type.name if next_type else None,
        "next_level_code": next_type.code if next_type else None,
        "progress_percentage": int(progress),
        "remaining_amount": int(remaining),
        "progress_text": progress_text,
        "benefits": benefits,
        "discount_percentage": float(current.discount_percentage or 0),
    }
