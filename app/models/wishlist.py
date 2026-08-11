from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="wishlists")
    product = relationship("Product")
