from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    cart_id = Column(BigInteger, ForeignKey("carts.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Numeric(12, 2), nullable=False, default=0)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

    @property
    def subtotal(self) -> float:
        return self.quantity * self.price
