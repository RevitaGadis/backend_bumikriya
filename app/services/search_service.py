from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.recipe import Recipe
from app.models.store import Store
from app.schemas.store import StoreSearchResult


def search_all(db: Session, q: str) -> dict:
    recipes = db.query(Recipe).filter(Recipe.title.ilike(f"%{q}%")).limit(10).all()

    products = db.query(Product).filter(Product.name.ilike(f"%{q}%")).limit(10).all()

    stores = db.query(Store).filter(Store.store_name.ilike(f"%{q}%")).limit(10).all()

    return {
        "recipes": recipes,
        "products": products,
        "stores": [StoreSearchResult(id=str(s.id), store_name=s.store_name, logo=s.logo, average_rating=0.0) for s in stores],
    }