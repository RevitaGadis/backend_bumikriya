import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.cart import Cart
from app.models.product import Product
from app.schemas.checkout import CheckoutRequest
from app.schemas.dashboard import OrderStatus, PaymentStatus


from app.services import membership_service

def _generate_order_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"


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

    subtotal = cart.total_price
    shipping_cost = Decimal(str(data.shipping_cost))
    total_amount = subtotal + shipping_cost

    db_order = Order(
        user_id=user_id,
        order_number=_generate_order_number(),
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total_amount=total_amount,
        status=OrderStatus.DIPROSES,
        shipping_address=data.shipping_address,
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

    db.delete(cart)

    db.commit()
    db.refresh(db_order)

    membership_service.add_spending(
        db, user_id, float(total_amount)
    )

    return db_order