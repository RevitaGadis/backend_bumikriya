import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.cart import Cart
from app.models.product import Product
from app.models.voucher import Voucher
from app.schemas.checkout import CheckoutRequest
from app.schemas.dashboard import OrderStatus, PaymentStatus


from app.services import membership_service

def _generate_order_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"


def _voucher_available(voucher: Voucher) -> Optional[str]:
    if not voucher.is_active:
        return "Voucher sudah tidak aktif"
    if voucher.valid_from and voucher.valid_from.tzinfo:
        now = datetime.now(voucher.valid_from.tzinfo)
    else:
        now = datetime.now()
    if voucher.valid_from and voucher.valid_from > now:
        return "Voucher belum berlaku"
    if voucher.valid_until and voucher.valid_until < now:
        return "Voucher sudah kadaluarsa"
    if voucher.quota and voucher.used_count >= voucher.quota:
        return "Kuota voucher sudah habis"
    return None


def apply_voucher(db: Session, code: str, subtotal: Decimal) -> Decimal:
    """Validasi voucher & hitung besar diskon. Raise HTTPException jika tidak valid."""
    voucher = db.query(Voucher).filter(Voucher.code == code).first()
    if not voucher:
        raise HTTPException(status_code=400, detail="Voucher tidak ditemukan")

    error = _voucher_available(voucher)
    if error:
        raise HTTPException(status_code=400, detail=error)

    if subtotal < Decimal(str(voucher.min_purchase)):
        raise HTTPException(
            status_code=400,
            detail=f"Minimal belanja Rp {int(voucher.min_purchase):,} untuk memakai voucher ini",
        )

    percent = Decimal(str(voucher.discount_percent)) / Decimal(100)
    discount = (subtotal * percent).quantize(Decimal("0.01"))
    if voucher.max_discount and discount > Decimal(str(voucher.max_discount)):
        discount = Decimal(str(voucher.max_discount))
    if discount > subtotal:
        discount = subtotal

    return discount


def checkout(db: Session, user_id: str, data: CheckoutRequest) -> Order:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Keranjang kosong")

    # validasi stok dulu
    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product or not product.is_active:
            raise HTTPException(status_code=400, detail="Produk tidak tersedia")
        if product.stock < cart_item.quantity:
            raise HTTPException(status_code=400, detail=f"Stok {product.name} tidak cukup")

    subtotal = Decimal(str(cart.total_price))
    shipping_cost = Decimal(str(data.shipping_cost))

    discount = Decimal("0.00")
    voucher = None
    if data.voucher_code and data.voucher_code.strip():
        discount = apply_voucher(db, data.voucher_code.strip(), subtotal)
        voucher = db.query(Voucher).filter(Voucher.code == data.voucher_code.strip()).first()

    total_amount = max(subtotal + shipping_cost - discount, Decimal("0.00"))

    db_order = Order(
        user_id=user_id,
        order_number=_generate_order_number(),
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        discount=discount,
        total_amount=total_amount,
        status=OrderStatus.DIPROSES,
        shipping_address=data.shipping_address,
        voucher_id=voucher.id if voucher else None,
    )
    db.add(db_order)
    db.flush()

    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        db.add(OrderItem(
            order_id=db_order.id,
            product_id=cart_item.product_id,
            product_name=product.name,
            price=cart_item.price,        # asumsi field ini ada di CartItem
            quantity=cart_item.quantity,
            subtotal=cart_item.subtotal,  # asumsi field ini ada di CartItem
        ))
        product.stock -= cart_item.quantity

    db.add(Payment(
        order_id=db_order.id,
        method=data.payment_method,
        amount=total_amount,
        status=PaymentStatus.PENDING,
    ))

    if voucher:
        voucher.used_count += 1
        db.add(voucher)

    db.delete(cart)

    db.commit()
    db.refresh(db_order)

    membership_service.add_spending(
        db, user_id, float(total_amount)
    )

    return db_order