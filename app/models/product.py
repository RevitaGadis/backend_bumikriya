from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
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
    seller_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("Category", back_populates="products")
    seller = relationship("User")