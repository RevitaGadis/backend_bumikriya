from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.recipe import Recipe, RecipeMaterial
from app.models.product import Product
from app.schemas.recipe import RecipeCreate, RecipeUpdate


def get_recipes(db: Session, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Recipe]:
    query = db.query(Recipe)
    if search:
        query = query.filter(Recipe.title.ilike(f"%{search}%"))
    return query.order_by(Recipe.created_at.desc()).offset(skip).limit(limit).all()


def get_recipe(db: Session, recipe_id: str) -> Optional[Recipe]:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def get_recommended_products(db: Session, category_id: str, exclude_id: Optional[str] = None, limit: int = 8) -> List[Product]:
    query = db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active.is_(True),
        Product.stock > 0,
    )
    if exclude_id:
        query = query.filter(Product.id != exclude_id)
    return query.limit(limit).all()


def _validate_materials(db: Session, materials: list) -> None:
    for m in materials:
        if m.suggested_product_id:
            product = db.query(Product).filter(Product.id == m.suggested_product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Produk {m.suggested_product_id} tidak ditemukan")


def create_recipe(db: Session, data: RecipeCreate) -> Recipe:
    _validate_materials(db, data.materials)

    db_recipe = Recipe(
        title=data.title,
        description=data.description,
        image=data.image,
        category_id=data.category_id,
    )
    db.add(db_recipe)
    db.flush()

    for m in data.materials:
        db.add(RecipeMaterial(
            recipe_id=db_recipe.id,
            category_id=m.category_id,
            material_name=m.material_name,
            quantity_needed=m.quantity_needed,
            unit=m.unit,
            note=m.note,
            suggested_product_id=m.suggested_product_id,
        ))

    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe(db: Session, recipe_id: str, data: RecipeUpdate) -> Optional[Recipe]:
    db_recipe = get_recipe(db, recipe_id)
    if not db_recipe:
        return None

    update_data = data.model_dump(exclude_unset=True, exclude={"materials"})
    for key, value in update_data.items():
        setattr(db_recipe, key, value)

    if data.materials is not None:
        _validate_materials(db, data.materials)
        db.query(RecipeMaterial).filter(RecipeMaterial.recipe_id == recipe_id).delete()
        for m in data.materials:
            db.add(RecipeMaterial(
                recipe_id=recipe_id,
                category_id=m.category_id,
                material_name=m.material_name,
                quantity_needed=m.quantity_needed,
                unit=m.unit,
                note=m.note,
                suggested_product_id=m.suggested_product_id,
            ))

    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def delete_recipe(db: Session, recipe_id: str) -> bool:
    db_recipe = get_recipe(db, recipe_id)
    if not db_recipe:
        return False
    db.delete(db_recipe)
    db.commit()
    return True


def search_all(db: Session, q: str) -> dict:
    from app.models.product import Product
    from app.models.store import Store
    from app.schemas.recipe import RecipeSummary, ProductBrief
    from app.schemas.store import StoreSearchResult

    # Search recipes
    recipes = db.query(Recipe).filter(Recipe.title.ilike(f"%{q}%")).limit(10).all()

    # Search products
    products = db.query(Product).filter(Product.name.ilike(f"%{q}%")).limit(10).all()

    # Search stores
    stores = db.query(Store).filter(Store.store_name.ilike(f"%{q}%")).limit(10).all()

    return {
        "recipes": recipes,
        "products": products,
        "stores": [StoreSearchResult(id=str(s.id), store_name=s.store_name, logo=s.logo, average_rating=0.0) for s in stores],
    }