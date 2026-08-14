import math
from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.schemas.dashboard import OrderStatus
from typing import Any, Optional


def _membership_for(total_spent: float, member_type=None):
    if member_type:
        return member_type
    if total_spent >= 10000000:
        return "Platinum"
    if total_spent >= 5000000:
        return "Gold"
    if total_spent >= 1000000:
        return "Silver"
    return "Bronze"


def _initial_for(name: str) -> str:
    if not name:
        return ""
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return parts[0][:2].upper() if parts else ""


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
            "initial": _initial_for(user.name),
            "avatar": user.photoprofil,
            "joined_at": user.created_at.date() if user.created_at else None,
            "total_orders": int(total_orders or 0),
            "total_spent": float(total_spent or 0),
            "status": "active",
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
            "avatar": user.photoprofil,
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

    growth_percentage = 0.0
    if last_month_count:
        growth_percentage = round(
            ((this_month_count - last_month_count) / last_month_count) * 100, 2
        )

    return {
        "customers": customers,
        "stats": {
            "active_customers": total_active_customers,
            "growth_percentage": growth_percentage,
        },
        "top_customer": top_customer,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        },
    }


def _map_order_status(status: OrderStatus) -> tuple:
    if status == OrderStatus.DIPROSES:
        return "processing", "Diproses"
    elif status == OrderStatus.DIKIRIM:
        return "shipped", "Dikirim"
    elif status == OrderStatus.SELESAI:
        return "completed", "Selesai"
    elif status == OrderStatus.DIBATALKAN:
        return "cancelled", "Dibatalkan"
    return status.value.lower(), status.value


def get_customer_detail(db: Session, customer_id: str) -> Optional[dict]:
    user = db.query(User).filter(User.id == customer_id, User.role.has(name="user")).first()
    if not user:
        return None

    orders_query = db.query(Order).filter(Order.user_id == customer_id)
    active_orders = [o for o in orders_query.all() if o.status != OrderStatus.DIBATALKAN]
    
    total_spent = sum(float(o.total_amount) for o in active_orders)
    total_orders = len(active_orders)
    average_order_value = total_spent / total_orders if total_orders > 0 else 0.0

    membership_name = _membership_for(total_spent, user.member_type)
    if not membership_name.lower().endswith("member"):
        membership_display_name = f"{membership_name} Member"
    else:
        membership_display_name = membership_name
    membership_level = membership_name.lower().replace(" member", "")

    recent_orders_list = (
        db.query(Order)
        .filter(Order.user_id == customer_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    recent_orders = []
    for order in recent_orders_list:
        status_code, _ = _map_order_status(order.status)
        recent_orders.append({
            "id": order.id,
            "order_number": order.order_number,
            "order_date": order.created_at.strftime("%Y-%m-%d") if order.created_at else "",
            "total": float(order.total_amount),
            "status": status_code,
        })

    avatar_path = user.photoprofil

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "avatar": avatar_path,
        "membership": {
            "name": membership_display_name,
            "level": membership_level
        },
        "joined_at": user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
        "summary": {
            "total_spent": total_spent,
            "total_orders": total_orders,
            "average_order_value": average_order_value
        },
        "recent_orders": recent_orders
    }


def update_customer(db: Session, customer_id: str, data: dict) -> Optional[dict]:
    user = db.query(User).filter(User.id == customer_id, User.role.has(name="user")).first()
    if not user:
        return None

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        existing = db.query(User).filter(User.email == data["email"], User.id != customer_id).first()
        if not existing:
            user.email = data["email"]
    if "phone" in data:
        user.phone = data["phone"]
    if "address" in data:
        user.address = data["address"]
    if "member_type" in data:
        user.member_type = data["member_type"]
    if "photoprofil" in data:
        user.photoprofil = data["photoprofil"]

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "avatar": user.photoprofil
    }


def get_customer_orders(db: Session, customer_id: str, page: int = 1, limit: int = 10) -> dict:
    query = db.query(Order).filter(Order.user_id == customer_id)
    total = query.count()
    total_pages = math.ceil(total / limit) if limit else 0

    rows = (
        query.order_by(Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    data = []
    for order in rows:
        status_code, status_label = _map_order_status(order.status)
        data.append({
            "id": order.id,
            "order_number": order.order_number,
            "order_date": order.created_at.strftime("%Y-%m-%d") if order.created_at else "",
            "total": float(order.total_amount),
            "status": status_code,
            "status_label": status_label
        })

    return {
        "orders": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


def get_admin_order_detail(db: Session, order_id: int) -> Optional[dict]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None

    user = order.user
    customer = {
        "id": user.id if user else "",
        "name": user.name if user else "Pelanggan Umum"
    }

    items = []
    for item in order.items:
        items.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "price": float(item.price),
            "subtotal": float(item.subtotal)
        })

    status_code, _ = _map_order_status(order.status)

    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer": customer,
        "order_date": order.created_at.strftime("%Y-%m-%d") if order.created_at else "",
        "status": status_code,
        "subtotal": float(order.subtotal),
        "shipping_cost": float(order.shipping_cost),
        "total": float(order.total_amount),
        "items": items
    }
