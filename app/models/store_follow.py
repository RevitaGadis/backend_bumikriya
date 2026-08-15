from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class StoreFollow(Base):
    __tablename__ = "store_follows"
    __table_args__ = (
        UniqueConstraint("store_id", "user_id", name="uq_store_follows_store_user"),
    )

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    store = relationship("Store", back_populates="follows")
    user = relationship("User")
