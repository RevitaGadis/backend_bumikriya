import midtransclient
import hashlib
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.config import settings
from app.models.payment import Payment
from app.models.order import Order
from app.schemas.dashboard import PaymentStatus, OrderStatus
from app.services import notification_service

snap = midtransclient.Snap(
    is_production=settings.MIDTRANS_IS_PRODUCTION,
    server_key=settings.MIDTRANS_SERVER_KEY,
    client_key=settings.MIDTRANS_CLIENT_KEY,
)


def create_snap_transaction(db: Session, order_id: int, user_id: str) -> dict:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = order.payment
    if not payment:
        raise HTTPException(status_code=400, detail="Payment record not found for this order")

    param = {
        "transaction_details": {
            "order_id": order.order_number,   # PENTING: pakai order_number, bukan order.id — harus unik & idempotent
            "gross_amount": int(order.total_amount),
        },
        "customer_details": {
            "first_name": order.user.name,
            "email": order.user.email,
        },
    }

    transaction = snap.create_transaction(param)

    payment.transaction_id = order.order_number  # simpan reference-nya
    db.add(payment)
    db.commit()

    return {
        "snap_token": transaction["token"],
        "redirect_url": transaction["redirect_url"],
    }

def handle_webhook(db: Session, payload: dict) -> dict:
    order_id = payload.get("order_id")            # ini order_number kamu
    status_code = payload.get("status_code")
    gross_amount = payload.get("gross_amount")
    signature_key = payload.get("signature_key")
    transaction_status = payload.get("transaction_status")

    # WAJIB: verifikasi signature, biar nggak bisa dipalsuin orang lain manggil webhook ini
    raw = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}"
    expected_signature = hashlib.sha512(raw.encode()).hexdigest()
    if signature_key != expected_signature:
        raise HTTPException(status_code=403, detail="Invalid signature")

    order = db.query(Order).filter(Order.order_number == order_id).first()
    if not order or not order.payment:
        raise HTTPException(status_code=404, detail="Order/Payment not found")

    payment = order.payment

    if transaction_status in ("capture", "settlement"):
        payment.status = PaymentStatus.PAID
        payment.paid_at = func.now()
        order.status = OrderStatus.DIPROSES  # atau status berikutnya sesuai alur kamu
    elif transaction_status in ("cancel", "deny", "expire"):
        payment.status = PaymentStatus.FAILED
    elif transaction_status == "pending":
        payment.status = PaymentStatus.PENDING

    db.add(payment)
    db.add(order)
    db.commit()

    if order.user_id:
        notification_service.create_notification(
            db=db,
            user_id=order.user_id,
            title="Update Pembayaran",
            message=f"Pembayaran order {order.order_number} berstatus {payment.status.value}",
            notification_type="payment",
            reference_type="order",
            reference_id=order.id,
        )

    return {"status": "ok"}