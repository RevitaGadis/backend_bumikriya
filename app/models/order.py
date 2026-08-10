from sqlalchemy import Column, DateTime, Enum, Float, String
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid
from app.schemas.dashboard import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer = Column(String(255), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DIPROSES)
    total = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
