from datetime import datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
from app.models.saving import Saving
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import OrderStatus
from app.schemas.transaction import TransactionType


def get_admin_dashboard(db: Session):
    today = datetime.now().date()
    today_start = datetime.combine(today, time.min)
    tomorrow_start = today_start + timedelta(days=1)
    week_start = today_start - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)

    valid_order_filter = Order.status != OrderStatus.DIBATALKAN
    total_sales = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == TransactionType.income
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
<<<<<<< HEAD
        weekly_totals[order.created_at.date()] += int(order.total)
=======
        weekly_totals[order.created_at.date()] += int(order.total_amount or 0)
>>>>>>> ff30657d9536d2185bba49004f52a59fbc43a492

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
<<<<<<< HEAD
                "customer": order.customer,
                "status": order.status.value,
                "total": int(order.total),
=======
                "customer": order.user.name if order.user else "Customer",
                "status": order.status.value,
                "total": int(order.total_amount or 0),
>>>>>>> ff30657d9536d2185bba49004f52a59fbc43a492
            }
            for order in recent_orders
        ],
    }


def get_user_dashboard(db: Session, user: User):
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == TransactionType.income,
    ).scalar() or 0.0
    total_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == TransactionType.expense,
    ).scalar() or 0.0
    total_saving_target = db.query(func.sum(Saving.target)).filter(
        Saving.user_id == user.id
    ).scalar() or 0.0
    total_saving_saved = db.query(func.sum(Saving.tersimpan)).filter(
        Saving.user_id == user.id
    ).scalar() or 0.0
    recent_transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.transaction_date.desc()).limit(5).all()

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name if user.role else None,
        },
        "total_transactions": db.query(Transaction).filter(Transaction.user_id == user.id).count(),
        "total_savings": db.query(Saving).filter(Saving.user_id == user.id).count(),
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "balance": float(total_income - total_expense),
        "total_saving_target": float(total_saving_target),
        "total_saving_saved": float(total_saving_saved),
        "recent_transactions": [
            {
                "id": transaction.id,
                "description": transaction.description,
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type.value,
                "transaction_date": transaction.transaction_date,
                "category": transaction.category_rel.name if transaction.category_rel else None,
            }
            for transaction in recent_transactions
        ],
    }
