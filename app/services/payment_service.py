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

    # Idempotent: kalau token Snap sudah pernah dibuat dan belum settle, kirim ulang token lama
    # supaya nggak memanggil Midtrans dengan order_id yang sama (error: order_id sudah digunakan).
    if payment.transaction_id and payment.snap_token and payment.status == PaymentStatus.PENDING:
        return {
            "snap_token": payment.snap_token,
            "redirect_url": payment.redirect_url,
        }

    # Transaksi sebelumnya gagal/expire => Midtrans menolak order_id yang sama.
    # Generate order_id unik untuk percobaan berikutnya, transaction_id jadi reference Midtrans-nya.
    attempt = 1
    if payment.transaction_id and payment.status != PaymentStatus.PENDING:
        prefix, _, last = payment.transaction_id.rpartition("-")
        previous_attempt = int(last) if last.isdigit() else 1
        attempt = previous_attempt + 1 if prefix else previous_attempt + 2
        midtrans_order_id = f"{order.order_number}-{attempt}"
    else:
        midtrans_order_id = order.order_number

    frontend_url = (settings.FRONTEND_URL or "").rstrip("/")

    param = {
        "transaction_details": {
            "order_id": midtrans_order_id,
            "gross_amount": int(order.total_amount),
        },
        "customer_details": {
            "first_name": order.user.name,
            "email": order.user.email,
        },
        "callbacks": {
            "finish": f"{frontend_url}/pesanan-saya",
            "error": f"{frontend_url}/keranjang",
        },
    }

    transaction = snap.create_transaction(param)

    payment.transaction_id = midtrans_order_id
    payment.snap_token = transaction["token"]
    payment.redirect_url = transaction["redirect_url"]
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
    if not order:
        # Pesan webhook mungkin membawa order_id percobaan ulang (mis: ORD-123-2)
        payment_lookup = (
            db.query(Payment)
            .filter(Payment.transaction_id == order_id)
            .first()
        )
        order = payment_lookup.order if payment_lookup else None

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