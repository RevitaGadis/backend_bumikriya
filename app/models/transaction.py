from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid
from app.schemas.dashboard import TransactionType


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False, default=0)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    note = Column(String(500), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    category_rel = relationship("Category", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
