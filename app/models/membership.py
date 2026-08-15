from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class MembershipType(Base):
    __tablename__ = "membership_types"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    min_spending = Column(Float, nullable=False, default=0)
    discount_percentage = Column(Float, nullable=False, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    benefits = relationship(
        "MembershipBenefit",
        back_populates="membership_type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user_memberships = relationship(
        "UserMembership", back_populates="membership_type"
    )


class UserMembership(Base):
    __tablename__ = "user_memberships"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        unique=True,
    )
    membership_type_id = Column(
        String(36),
        ForeignKey("membership_types.id"),
        nullable=False,
        index=True,
    )
    total_spending = Column(Float, nullable=False, default=0)
    started_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="membership")
    membership_type = relationship(
        "MembershipType", back_populates="user_memberships"
    )


class MembershipBenefit(Base):
    __tablename__ = "membership_benefits"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    membership_type_id = Column(
        String(36),
        ForeignKey("membership_types.id"),
        nullable=False,
        index=True,
    )
    benefit = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    membership_type = relationship(
        "MembershipType", back_populates="benefits"
    )
