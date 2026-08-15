from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.review import Review
from app.models.order_item import OrderItem
from app.models.order import Order
from app.schemas.dashboard import OrderStatus
from app.schemas.review import ReviewCreate


def get_reviews_by_product(db: Session, product_id: str) -> List[Review]:
    return db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()


def create_review(db: Session, user_id: str, review_in: ReviewCreate) -> Review:
    order_item = db.query(OrderItem).filter(OrderItem.id == review_in.order_item_id).first()
    if not order_item:
        raise HTTPException(status_code=404, detail="Item pesanan tidak ditemukan")

    order = db.query(Order).filter(Order.id == order_item.order_id).first()
    if not order or order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Ini bukan pesanan kamu")
    if order.status != OrderStatus.SELESAI:
        raise HTTPException(status_code=400, detail="Hanya bisa review pesanan yang sudah selesai")

    existing = db.query(Review).filter(Review.order_item_id == review_in.order_item_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sudah pernah review item ini")

    db_review = Review(
        product_id=order_item.product_id,
        user_id=user_id,
        order_item_id=review_in.order_item_id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review