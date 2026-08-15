from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.membership import (
    MembershipType,
    UserMembership,
    MembershipBenefit,
)
from app.models.user import User


def format_rupiah(amount: float) -> str:
    return "Rp {:,}".format(int(round(amount))).replace(",", ".")


DEFAULT_MEMBERSHIP_TYPES = [
    {
        "name": "Bronze Member",
        "code": "bronze",
        "min_spending": 0,
        "discount_percentage": 0,
        "description": "Level keanggotaan dasar",
        "benefits": [
            "Poin reward untuk setiap pembelian",
            "Akses ke koleksi dasar",
        ],
    },
    {
        "name": "Silver Member",
        "code": "silver",
        "min_spending": 500000,
        "discount_percentage": 3,
        "description": "Level keanggotaan menengah",
        "benefits": [
            "Diskon 3% untuk semua produk",
            "Gratis ongkir untuk pembelian di atas Rp 300.000",
            "Akses ke koleksi baru",
        ],
    },
    {
        "name": "Gold Member",
        "code": "gold",
        "min_spending": 1000000,
        "discount_percentage": 5,
        "description": "Level keanggotaan premium",
        "benefits": [
            "Diskon 5% untuk semua produk",
            "Gratis ongkir setiap akhir pekan",
            "Akses awal ke koleksi baru",
            "Undangan eksklusif workshop",
        ],
    },
    {
        "name": "Platinum Member",
        "code": "platinum",
        "min_spending": 3000000,
        "discount_percentage": 10,
        "description": "Level keanggotaan tertinggi",
        "benefits": [
            "Diskon 10% untuk semua produk",
            "Gratis ongkir tanpa syarat",
            "Akses prioritas ke koleksi baru",
            "Undangan eksklusif workshop dan event",
            "Layanan konsultasi personal",
        ],
    },
]


def get_membership_types(db: Session) -> List[MembershipType]:
    return (
        db.query(MembershipType)
        .order_by(MembershipType.min_spending.asc())
        .all()
    )


def get_membership_type_by_code(db: Session, code: str) -> Optional[MembershipType]:
    return db.query(MembershipType).filter(MembershipType.code == code).first()


def ensure_default_membership_types(db: Session) -> None:
    for data in DEFAULT_MEMBERSHIP_TYPES:
        existing = get_membership_type_by_code(db, code=data["code"])
        if existing:
            continue
        membership_type = MembershipType(
            name=data["name"],
            code=data["code"],
            min_spending=data["min_spending"],
            discount_percentage=data["discount_percentage"],
            description=data["description"],
        )
        db.add(membership_type)
        db.flush()
        for benefit_text in data["benefits"]:
            db.add(
                MembershipBenefit(
                    membership_type_id=membership_type.id,
                    benefit=benefit_text,
                )
            )
    db.commit()

    legacy_basic = get_membership_type_by_code(db, code="basic")
    bronze = get_membership_type_by_code(db, code="bronze")
    if legacy_basic and bronze:
        db.query(UserMembership).filter(
            UserMembership.membership_type_id == legacy_basic.id
        ).update({UserMembership.membership_type_id: bronze.id})
        db.query(MembershipBenefit).filter(
            MembershipBenefit.membership_type_id == legacy_basic.id
        ).delete()
        db.delete(legacy_basic)
        db.commit()


def get_or_create_default_membership_type(db: Session) -> Optional[MembershipType]:
    ensure_default_membership_types(db)
    default_type = (
        db.query(MembershipType)
        .order_by(MembershipType.min_spending.asc())
        .first()
    )
    if default_type:
        return default_type
    return None


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


def _normalize_key(value) -> str:
    return "".join(str(value or "").lower().replace("_", "").replace("-", "").split())


def match_membership_type(
    types: List[MembershipType], member_type
) -> Optional[MembershipType]:
    key = _normalize_key(member_type)
    if not key:
        return None

    if key in ("regular", "regularmember", "basic", "basicmember", "member"):
        return types[0] if types else None
    if key in ("bronze", "bronzemember", "silver", "silvermember", "gold", "goldmember", "platinum", "platinummember"):
        for t in types:
            if t.code == key or _normalize_key(t.name) == key:
                return t
        return None
    return None


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
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return None
        um = ensure_user_membership(db, user)
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
    current = match_membership_type(types, getattr(user, "member_type", None))
    if current is None:
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
