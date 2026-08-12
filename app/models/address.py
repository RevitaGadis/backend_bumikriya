from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class Address(Base):
    __tablename__ = "addresses"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    label = Column(String(50), nullable=False, default="Rumah")  # mis. "Rumah", "Kantor", "Kos"
    recipient_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)

    address_line = Column(String(500), nullable=False)   # nama jalan, no rumah, RT/RW, patokan
    kelurahan = Column(String(100), nullable=True)
    kecamatan = Column(String(100), nullable=True)
    kota = Column(String(100), nullable=False)
    provinsi = Column(String(100), nullable=False)
    kode_pos = Column(String(10), nullable=True)

    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="addresses")