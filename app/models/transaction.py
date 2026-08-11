from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid
from app.schemas.transaction import TransactionType

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    note = Column(String(500), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"))

    user = relationship("User", back_populates="transactions")
    category_rel = relationship("Category", back_populates="transactions")
