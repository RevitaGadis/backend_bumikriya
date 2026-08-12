from sqlalchemy import Boolean, Column, Float, Integer, String

from app.db.base import Base, generate_uuid


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False, default=0)
    image = Column(String(255), nullable=False)
    color = Column(String(255), nullable=False)
    material = Column(String(255), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    fits = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
