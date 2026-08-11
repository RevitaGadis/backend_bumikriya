import math
from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.schemas.dashboard import OrderStatus


def _membership_for(total_spent: float, member_type=None):
    if member_type:
        return member_type
    if total_spent >= 10000000:
        return "Platinum Member"
    if total_spent >= 5000000:
        return "Gold Member"
    if total_spent >= 1000000:
        return "Silver Member"
    return "Member"


def _order_stats(db: Session):
    return (
        db.query(
            Order.user_id.label("user_id"),
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total_amount), 0).label("total_spent"),
        )
        .filter(Order.status != OrderStatus.DIBATALKAN)
        .group_by(Order.user_id)
        .subquery()
    )


def get_customers(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str = None,
) -> dict:
    stats = _order_stats(db)

    query = (
        db.query(User, stats.c.total_orders, stats.c.total_spent)
        .outerjoin(stats, stats.c.user_id == User.id)
        .filter(User.role.has(name="user"))
    )

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
        query.order_by(func.coalesce(stats.c.total_spent, 0).desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    customers = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": None,
            "join_date": user.created_at.date() if user.created_at else None,
            "total_orders": int(total_orders or 0),
            "total_spent": float(total_spent or 0),
            "membership": _membership_for(float(total_spent or 0), user.member_type),
        }
        for user, total_orders, total_spent in rows
    ]

    top = (
        db.query(User, stats.c.total_orders, stats.c.total_spent)
        .join(stats, stats.c.user_id == User.id)
        .filter(User.role.has(name="user"))
        .order_by(stats.c.total_spent.desc())
        .first()
    )

    top_customer = None
    if top:
        user, total_orders, total_spent = top
        top_customer = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": None,
            "membership": _membership_for(float(total_spent or 0), user.member_type),
            "total_spent": float(total_spent or 0),
            "total_orders": int(total_orders or 0),
        }

    total_active_customers = (
        db.query(func.count(User.id)).filter(User.role.has(name="user")).scalar() or 0
    )

    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = datetime(prev_month_end.year, prev_month_end.month, 1)

    last_month_count = (
        db.query(func.count(User.id))
        .filter(
            User.role.has(name="user"),
            User.created_at >= prev_month_start,
            User.created_at < month_start,
        )
        .scalar()
        or 0
    )
    this_month_count = (
        db.query(func.count(User.id))
        .filter(
            User.role.has(name="user"),
            User.created_at >= month_start,
        )
        .scalar()
        or 0
    )

    growth_percentage = 0
    if last_month_count:
        growth_percentage = int(
            ((this_month_count - last_month_count) / last_month_count) * 100
        )

    return {
        "customers": customers,
        "statistics": {
            "total_active_customers": total_active_customers,
            "growth_percentage": growth_percentage,
            "growth_period": "month",
        },
        "top_customer": top_customer,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        },
    }
