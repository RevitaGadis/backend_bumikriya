from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.schemas.dashboard import PaymentMethod, PaymentStatus


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    method = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    transaction_id = Column(String(100), nullable=True)
    snap_token = Column(String(200), nullable=True)
    redirect_url = Column(String(500), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    order = relationship("Order", back_populates="payment")
