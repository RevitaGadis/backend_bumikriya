from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Saving(Base):
    __tablename__ = "savings"

    id          = Column(Integer, primary_key=True, index=True)
    nama        = Column(String(255), nullable=False)
    target      = Column(Float, nullable=False)
    tersimpan   = Column(Float, default=0)
    deadline    = Column(Date, nullable=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="savings")
