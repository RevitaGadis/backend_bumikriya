from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product


def get_cart(db: Session, user_id: str) -> Optional[Cart]:
    return db.query(Cart).filter(Cart.user_id == user_id).first()


def get_or_create_cart(db: Session, user_id: str) -> Cart:
    cart = get_cart(db, user_id)
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def add_item(db: Session, user_id: str, product_id: str, quantity: int) -> Cart:
    cart = get_or_create_cart(db, user_id)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan atau tidak aktif")
    if product.seller_id == user_id:
        raise HTTPException(status_code=400, detail="Tidak bisa membeli produk milik toko sendiri")
    if quantity > product.stock:
        raise HTTPException(status_code=400, detail=f"Stok {product.name} tidak cukup (tersisa {product.stock})")

    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )
    if item:
        new_quantity = item.quantity + quantity
        if new_quantity > product.stock:
            raise HTTPException(status_code=400, detail=f"Stok {product.name} tidak cukup (tersisa {product.stock})")
        item.quantity = new_quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
            price=product.price,
        )
        db.add(item)

    db.commit()
    return get_cart(db, user_id)


def update_item_quantity(db: Session, user_id: str, item_id: int, quantity: int) -> Cart:
    cart = get_cart(db, user_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart tidak ditemukan")
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan di cart")
    if quantity > item.product.stock:
        raise HTTPException(status_code=400, detail=f"Stok tidak cukup (tersisa {item.product.stock})")
    item.quantity = quantity
    db.commit()
    return get_cart(db, user_id)


def remove_item(db: Session, user_id: str, item_id: int) -> bool:
    cart = get_cart(db, user_id)
    if not cart:
        return False
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def clear_cart(db: Session, user_id: str) -> bool:
    cart = get_cart(db, user_id)
    if not cart:
        return False
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return True