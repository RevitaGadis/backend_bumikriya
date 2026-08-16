from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func, BigInteger
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    order_item_id = Column(BigInteger, ForeignKey("order_items.id"), nullable=False, unique=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product")
    user = relationship("User")