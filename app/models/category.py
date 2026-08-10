from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid

class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    transactions = relationship("Transaction", back_populates="category_rel")
