from datetime import datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.role import Role
from app.models.store import Store
from app.models.user import User
from app.schemas.dashboard import OrderStatus

STATUS_LABELS = {
    OrderStatus.DIPROSES: "processing",
    OrderStatus.DIKIRIM: "shipping",
    OrderStatus.SELESAI: "completed",
    OrderStatus.DIBATALKAN: "cancelled",
}


def _seller_display_name(seller: User) -> str:
    store = seller.store
    if store and store.store_name:
        return store.store_name
    return seller.name or "Penjual"


def get_admin_dashboard(db: Session):
    today = datetime.now().date()
    today_start = datetime.combine(today, time.min)
    tomorrow_start = today_start + timedelta(days=1)

    valid_order_filter = Order.status != OrderStatus.DIBATALKAN

    total_seller = (
        db.query(User)
        .join(Role, Role.id == User.role_id)
        .filter(Role.name == "seller")
        .count()
    )
    pesanan_baru = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.created_at < tomorrow_start,
    ).count()
    produk_aktif = db.query(Product).filter(Product.is_active.is_(True)).count()

    summary = {
        "total_seller": total_seller,
        "pesanan_baru": pesanan_baru,
        "produk_aktif": produk_aktif,
    }

    top_seller_rows = (
        db.query(
            User,
            func.count(func.distinct(Order.id)).label("total_orders"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_products_sold"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("total_revenue"),
        )
        .join(Store, Store.user_id == User.id)
        .join(Product, Product.seller_id == User.id)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(valid_order_filter)
        .group_by(User.id, User.name)
        .order_by(func.sum(OrderItem.subtotal).desc())
        .limit(5)
        .all()
    )

    top_sellers = [
        {
            "seller_id": seller.id,
            "seller_name": _seller_display_name(seller),
            "total_orders": int(total_orders),
            "total_products_sold": int(total_products_sold),
            "total_revenue": int(total_revenue),
        }
        for seller, total_orders, total_products_sold, total_revenue in top_seller_rows
    ]

    recent_orders = db.query(Order).order_by(Order.created_at.desc(), Order.id.desc()).limit(10).all()

    latest_orders = []
    for order in recent_orders:
        seller_name = "Penjual"
        for item in order.items:
            if item.product and item.product.seller:
                seller_name = _seller_display_name(item.product.seller)
                break

        latest_orders.append(
            {
                "order_id": order.order_number,
                "customer_name": order.user.name if order.user else "Customer",
                "seller_name": seller_name,
                "total_amount": int(order.total_amount or 0),
                "status": STATUS_LABELS.get(order.status, order.status.value if order.status else ""),
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        )

    return {
        "summary": summary,
        "top_sellers": top_sellers,
        "latest_orders": latest_orders,
    }