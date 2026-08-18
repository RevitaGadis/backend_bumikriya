from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, func, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    photoprofil = Column(String(255), nullable=True)
    member_type = Column(String(50), nullable=True)
    is_admin = Column(Boolean, default=False)
    status = Column(String(20), nullable=False, default="active", server_default="active")
    is_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    role = relationship("Role", back_populates="users")
    orders = relationship("Order", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    wishlists = relationship("Wishlist", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    store = relationship("Store", back_populates="user", uselist=False)
    addresses = relationship("Address", back_populates="user")
    membership = relationship(
        "UserMembership", back_populates="user", uselist=False
    )
    vouchers = relationship("UserVoucher", back_populates="user", cascade="all, delete-orphan")
