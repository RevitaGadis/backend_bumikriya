from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class UserVoucher(Base):
    """Penautan voucher hadiah (reward keanggotaan) ke pengguna tertentu."""

    __tablename__ = "user_vouchers"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    voucher_id = Column(
        String(36),
        ForeignKey("vouchers.id"),
        nullable=False,
        index=True,
    )
    level_code = Column(String(50), nullable=True, index=True)
    is_claimed = Column(Boolean, nullable=False, default=False)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="vouchers")
    voucher = relationship("Voucher", back_populates="user_vouchers")


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    discount_percent = Column(Numeric(5, 2), nullable=False, default=0)
    max_discount = Column(Numeric(12, 2), nullable=True)
    min_purchase = Column(Numeric(12, 2), nullable=False, default=0)
    quota = Column(Integer, nullable=False, default=0)
    used_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    creator = relationship("User", foreign_keys=[created_by])
    orders = relationship("Order", back_populates="voucher")
    user_vouchers = relationship("UserVoucher", back_populates="voucher", cascade="all, delete-orphan")