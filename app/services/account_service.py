import math
from typing import Optional

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User


def _role_name(user: User) -> str:
    if user.role and user.role.name:
        return user.role.name
    return "admin" if user.is_admin else "user"


def _avatar_url(photoprofil: Optional[str]) -> Optional[str]:
    if not photoprofil:
        return None
    if photoprofil.startswith("http://") or photoprofil.startswith("https://"):
        return photoprofil
    return f"{settings.BASE_URL}{photoprofil}"


def _serialize(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": _avatar_url(user.photoprofil),
        "role": _role_name(user),
        "status": user.status,
        "is_verified": user.is_verified,
    }


def _serialize_detail(user: User) -> dict:
    data = _serialize(user)
    data["created_at"] = user.created_at
    data["updated_at"] = user.updated_at
    return data


def _staff_filter():
    return or_(
        User.role.has(Role.name.in_(["admin", "seller"])),
        User.is_admin.is_(True),
    )


def get_accounts(db: Session, page: int = 1, limit: int = 10, search: Optional[str] = None) -> dict:
    query = db.query(User).filter(_staff_filter())

    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    total_pages = math.ceil(total / limit) if limit else 0

    rows = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [_serialize(u) for u in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total,
            "total_pages": total_pages,
        },
    }


def get_account_summary(db: Session) -> dict:
    total_accounts = db.query(func.count(User.id)).scalar() or 0
    total_verified = db.query(func.count(User.id)).filter(User.is_verified.is_(True)).scalar() or 0

    role_expr = case(
        (Role.name.isnot(None), Role.name),
        (User.is_admin.is_(True), "admin"),
        else_="user",
    )
    role_rows = (
        db.query(role_expr, func.count(User.id))
        .outerjoin(Role, User.role_id == Role.id)
        .group_by(role_expr)
        .all()
    )
    role_distribution = {name: int(count) for name, count in role_rows}

    status_rows = db.query(User.status, func.count(User.id)).group_by(User.status).all()
    status_distribution = {name: int(count) for name, count in status_rows}

    return {
        "total_accounts": total_accounts,
        "total_verified": total_verified,
        "role_distribution": role_distribution,
        "status_distribution": status_distribution,
    }


def get_account_detail(db: Session, account_id: str) -> Optional[dict]:
    user = db.query(User).filter(User.id == account_id).first()
    if not user:
        return None
    return _serialize_detail(user)


def create_account(db: Session, data: dict) -> dict:
    role_name = data.get("role") or "seller"
    role = db.query(Role).filter(Role.name == role_name).first()

    db_user = User(
        name=data["name"],
        email=data["email"],
        hashed_password=get_password_hash(data["password"]),
        photoprofil=data.get("photoprofil"),
        is_admin=(role_name == "admin"),
        role_id=role.id if role else None,
        status="active",
        is_verified=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return _serialize_detail(db_user)


def update_account(db: Session, account_id: str, data: dict) -> Optional[dict]:
    user = db.query(User).filter(User.id == account_id).first()
    if not user:
        return None

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        existing = db.query(User).filter(
            User.email == data["email"], User.id != account_id
        ).first()
        if existing:
            raise ValueError("Email sudah digunakan")
        user.email = data["email"]
    if "role" in data:
        role_name = data["role"]
        role = db.query(Role).filter(Role.name == role_name).first()
        user.role_id = role.id if role else None
        user.is_admin = role_name == "admin"
    if "status" in data:
        user.status = data["status"]
    if "photoprofil" in data:
        user.photoprofil = data["photoprofil"]
    if data.get("remove_avatar"):
        user.photoprofil = None

    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_detail(user)


def update_account_status(db: Session, account_id: str, status_value: str) -> Optional[dict]:
    if status_value not in ("active", "inactive"):
        raise ValueError("Status harus 'active' atau 'inactive'")
    user = db.query(User).filter(User.id == account_id).first()
    if not user:
        return None
    user.status = status_value
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_detail(user)
