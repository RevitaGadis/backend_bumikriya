from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image = Column(String(255), nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("Category")
    materials = relationship("RecipeMaterial", back_populates="recipe", cascade="all, delete-orphan")


class RecipeMaterial(Base):
    __tablename__ = "recipe_materials"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    recipe_id = Column(String(36), ForeignKey("recipes.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False, index=True)
    material_name = Column(String(150), nullable=False)
    quantity_needed = Column(Float, nullable=False, default=1)
    unit = Column(String(30), nullable=True)
    note = Column(String(255), nullable=True)
    suggested_product_id = Column(String(36), ForeignKey("products.id"), nullable=True, index=True)

    recipe = relationship("Recipe", back_populates="materials")
    category = relationship("Category")
    suggested_product = relationship("Product")