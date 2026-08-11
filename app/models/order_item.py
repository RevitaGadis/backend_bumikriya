from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
