from datetime import datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.dashboard import OrderStatus

def get_admin_dashboard(db: Session):
    today = datetime.now().date()
    today_start = datetime.combine(today, time.min)
    tomorrow_start = today_start + timedelta(days=1)
    week_start = today_start - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)

    valid_order_filter = Order.status != OrderStatus.DIBATALKAN
    total_sales = db.query(func.sum(Order.total_amount)).filter(
        valid_order_filter
    ).scalar() or 0
    new_orders = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.created_at < tomorrow_start,
    ).count()
    active_products = db.query(Product).filter(Product.is_active.is_(True)).count()
    weekly_orders = db.query(Order).filter(
        valid_order_filter,
        Order.created_at >= week_start,
        Order.created_at < week_end,
    ).all()

    weekly_totals = {week_start.date() + timedelta(days=idx): 0 for idx in range(7)}
    for order in weekly_orders:
        weekly_totals[order.created_at.date()] += int(order.total_amount or 0)

    day_names = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    recent_orders = db.query(Order).order_by(Order.created_at.desc(), Order.id.desc()).limit(5).all()

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