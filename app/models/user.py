from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=True, index=True)

    role = relationship("Role", back_populates="users")
    transactions = relationship("Transaction", back_populates="user")
    savings = relationship("Saving", back_populates="user")
