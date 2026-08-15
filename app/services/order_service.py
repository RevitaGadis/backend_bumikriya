from datetime import datetime, time, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderDetail, OrderUpdate
from app.schemas.dashboard import OrderStatus, PaymentMethod, PaymentStatus
from app.services import notification_service

STATUS_LABELS = {
    OrderStatus.DIPROSES: ("processing", "Diproses"),
    OrderStatus.DIKIRIM: ("shipping", "Dikirim"),
    OrderStatus.SELESAI: ("completed", "Selesai"),
    OrderStatus.DIBATALKAN: ("cancelled", "Dibatalkan"),
}

STATUS_HISTORY_LABELS = {
    OrderStatus.DIPROSES: "Sedang Diproses",
    OrderStatus.DIKIRIM: "Sedang Dikirim",
    OrderStatus.SELESAI: "Pesanan Selesai",
    OrderStatus.DIBATALKAN: "Pesanan Dibatalkan",
}

SHIPPING_STATUS = {
    OrderStatus.DIPROSES: "processing",
    OrderStatus.DIKIRIM: "shipping",
    OrderStatus.SELESAI: "delivered",
    OrderStatus.DIBATALKAN: "cancelled",
}

PAYMENT_STATUS_LABELS = {
    PaymentStatus.PENDING: "pending",
    PaymentStatus.PAID: "paid",
    PaymentStatus.FAILED: "failed",
    PaymentStatus.REFUNDED: "refunded",
}

PAYMENT_METHOD_LABELS = {
    PaymentMethod.CASH: "Cash",
    PaymentMethod.TRANSFER: "Transfer",
    PaymentMethod.OVO: "OVO",
    PaymentMethod.GOPAY: "GoPay",
    PaymentMethod.DANA: "DANA",
    PaymentMethod.SHOPEEPAY: "ShopeePay",
    PaymentMethod.COD: "COD",
}


def get_order(db: Session, order_id: str) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_detail(db: Session, order_id: str) -> Optional[OrderDetail]:
    order = get_order(db, order_id)
    if not order:
        return None

    code, label = STATUS_LABELS.get(order.status, (order.status.value, order.status.value))

    user = order.user
    customer = {
        "id": user.id if user else None,
        "name": user.name if user else "",
        "email": user.email if user else None,
        "phone": user.phone if user else None,
        "type": user.member_type if user else None,
        "avatar": None,
        "shipping_address": {
            "recipient_name": user.name if user else None,
            "address": order.shipping_address or None,
            "city": None,
            "province": None,
            "postal_code": None,
        },
    }

    items = []
    for item in order.items:
        product = item.product
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "sku": None,
                "image": product.image if product else None,
                "price": float(item.price),
                "quantity": item.quantity,
                "subtotal": float(item.subtotal),
            }
        )

    payment = order.payment
    payment_data = {
        "subtotal": float(order.subtotal),
        "shipping_cost": float(order.shipping_cost),
        "discount": float(order.discount),
        "total": float(order.total_amount),
        "payment_method": PAYMENT_METHOD_LABELS.get(payment.method) if payment else None,
        "payment_status": PAYMENT_STATUS_LABELS.get(payment.status) if payment else None,
        "paid_at": payment.paid_at if payment else None,
        "voucher": (
            {
                "id": order.voucher.id,
                "code": order.voucher.code,
                "name": order.voucher.name,
                "discount_percent": float(order.voucher.discount_percent),
            }
            if order.voucher
            else None
        ),
    }

    shipping_data = {
        "courier": None,
        "tracking_number": None,
        "shipping_status": SHIPPING_STATUS.get(order.status, "pending"),
    }

    status_history = [
        {
            "status": code,
            "label": label,
            "created_at": order.created_at,
        }
    ]
    if payment and payment.paid_at:
        status_history.append(
            {
                "status": "paid",
                "label": "Pembayaran Diterima",
                "created_at": payment.paid_at,
            }
        )
    status_history.append(
        {
            "status": "created",
            "label": "Pesanan Dibuat",
            "created_at": order.created_at,
        }
    )

    return OrderDetail(
        id=order.id,
        order_number=order.order_number,
        status={"code": code, "label": label},
        customer=customer,
        items=items,
        payment=payment_data,
        shipping=shipping_data,
        status_history=status_history,
        created_at=order.created_at,
        updated_at=None,
    )


def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
    return db.query(Order).filter(Order.order_number == order_number).first()


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
) -> List[Order]:
    query = db.query(Order)
    if user_id:
        query = query.filter(Order.user_id == user_id)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def update_order(db: Session, order_id: str, order: OrderUpdate) -> Optional[Order]:
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    update_data = order.model_dump(exclude_unset=True)
    status_changed = order.status is not None and order.status != db_order.status
    for key, value in update_data.items():
        setattr(db_order, key, value)

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    if status_changed and db_order.user_id:
        label = STATUS_HISTORY_LABELS.get(
            db_order.status, db_order.status.value if db_order.status else ""
        )
        notification_service.create_notification(
            db=db,
            user_id=db_order.user_id,
            title="Update Status Pesanan",
            message=f"Pesanan {db_order.order_number} berstatus {label}",
            notification_type="order",
            reference_type="order",
            reference_id=db_order.id,
        )
    return db_order


def _seller_orders_query(db: Session, seller_id: str):
    return (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Product.seller_id == seller_id)
        .distinct()
    )


def get_orders_for_seller(
    db: Session,
    seller_id: str,
    skip: int = 0,
    limit: int = 100,
) -> List[dict]:
    """List order yang mengandung minimal satu produk milik seller. (Seller only)"""
    orders = (
        _seller_orders_query(db, seller_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for order in orders:
        status_code, status_label = STATUS_LABELS.get(
            order.status, (order.status.value, order.status.value)
        )
        result.append(
            {
                "id": order.id,
                "order_number": order.order_number,
                "order_date": order.created_at.strftime("%Y-%m-%d") if order.created_at else "",
                "total": float(order.total_amount),
                "status": status_code,
                "status_label": status_label,
                "customer": {
                    "id": order.user_id,
                    "name": order.user.name if order.user else "",
                },
                "items": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "subtotal": float(item.subtotal),
                    }
                    for item in order.items
                    if item.product and item.product.seller_id == seller_id
                ],
            }
        )
    return result


def update_seller_order_status(
    db: Session,
    order_id: int,
    seller_id: str,
    status: OrderStatus,
) -> Optional[Order]:
    """Update status order hanya jika berisi minimal satu produk milik seller."""
    order = (
        _seller_orders_query(db, seller_id)
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        return None

    old_status = order.status
    order.status = status
    db.add(order)
    db.commit()
    db.refresh(order)

    if status != old_status and order.user_id:
        label = STATUS_HISTORY_LABELS.get(status, status.value if status else "")
        notification_service.create_notification(
            db=db,
            user_id=order.user_id,
            title="Update Status Pesanan",
            message=f"Pesanan {order.order_number} berstatus {label}",
            notification_type="order",
            reference_type="order",
            reference_id=order.id,
        )
    return order


def get_seller_dashboard_summary(db: Session, seller_id: str) -> dict:
    """Ringkasan performa toko milik seller. (Seller only)"""
    today = datetime.now().date()
    today_start = datetime.combine(today, time.min)
    tomorrow_start = today_start + timedelta(days=1)
    week_start = today_start - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)

    valid_orders = _seller_orders_query(db, seller_id).filter(
        Order.status != OrderStatus.DIBATALKAN
    )

    total_sales = (
        valid_orders.with_entities(func.sum(Order.total_amount)).scalar() or 0
    )

    new_orders = _seller_orders_query(db, seller_id).filter(
        Order.created_at >= today_start,
        Order.created_at < tomorrow_start,
    ).count()

    active_products = db.query(Product).filter(
        Product.seller_id == seller_id,
        Product.is_active.is_(True),
    ).count()

    weekly_orders = valid_orders.filter(
        Order.created_at >= week_start,
        Order.created_at < week_end,
    ).all()

    weekly_totals = {week_start.date() + timedelta(days=idx): 0 for idx in range(7)}
    for order in weekly_orders:
        weekly_totals[order.created_at.date()] += int(order.total_amount or 0)

    day_names = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    recent_orders = _seller_orders_query(db, seller_id).order_by(
        Order.created_at.desc(), Order.id.desc()
    ).limit(5).all()

    return {
        "total_sales": int(total_sales),
        "new_orders": new_orders,
        "active_products": active_products,
        "weekly_sales": [
            {
                "day": day_names[idx],
                "total": weekly_totals[week_start.date() + timedelta(days=idx)],
            }
            for idx in range(7)
        ],
        "recent_orders": [
            {
                "order_number": order.order_number,
                "customer": order.user.name if order.user else "Customer",
                "status": order.status.value,
                "total": int(order.total_amount or 0),
            }
            for order in recent_orders
        ],
    }

