<<<<<<< HEAD
from sqlalchemy import Column, DateTime, Enum, Float, String
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid
=======
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base
>>>>>>> ff30657d9536d2185bba49004f52a59fbc43a492
from app.schemas.dashboard import OrderStatus


class Order(Base):
    __tablename__ = "orders"

<<<<<<< HEAD
    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer = Column(String(255), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DIPROSES)
    total = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
=======
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    shipping_cost = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DIPROSES)
    shipping_address = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="orders")
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
>>>>>>> ff30657d9536d2185bba49004f52a59fbc43a492
