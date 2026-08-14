from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.schemas.dashboard import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    shipping_cost = Column(Numeric(12, 2), nullable=False, default=0)
    discount = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DIPROSES)
    shipping_address = Column(Text, nullable=False)
    voucher_id = Column(String(36), ForeignKey("vouchers.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="orders")
    voucher = relationship("Voucher", back_populates="orders", uselist=False, lazy="selectin")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    payment = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
