from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid


class Store(Base):
    __tablename__ = "stores"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    store_name = Column(String(150), nullable=False)
    tagline = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    logo = Column(String(255), nullable=True)
    banner = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    shipping_policy = Column(Text, nullable=True)
    return_policy = Column(Text, nullable=True)
    custom_policy = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="store")
    follows = relationship("StoreFollow", back_populates="store", cascade="all, delete-orphan")