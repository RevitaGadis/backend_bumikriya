from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")
