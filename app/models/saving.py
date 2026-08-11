from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid

class Saving(Base):
    __tablename__ = "savings"

    id          = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    nama        = Column(String(255), nullable=False)
    target      = Column(Float, nullable=False)
    tersimpan   = Column(Float, default=0)
    deadline    = Column(Date, nullable=True)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="savings")
