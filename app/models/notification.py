from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="general", index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(String(50), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="notifications")
