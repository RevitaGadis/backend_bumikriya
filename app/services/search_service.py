from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.recipe import Recipe
from app.models.store import Store
from app.services import store_service


def search_all(db: Session, keyword: str, limit: int = 10) -> dict:
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.name.ilike(f"%{keyword}%"))
        .limit(limit)
        .all()
    )
    recipes = (
        db.query(Recipe)
        .filter(Recipe.title.ilike(f"%{keyword}%"))
        .limit(limit)
        .all()
    )
    stores = (
        db.query(Store)
        .filter(Store.is_approved.is_(True), Store.store_name.ilike(f"%{keyword}%"))
        .limit(limit)
        .all()
    )

    stores_out = []
    for store in stores:
        rating = store_service.get_store_rating_summary(db, store.user_id)
        stores_out.append({
            "id": store.id,
            "store_name": store.store_name,
            "logo": store.logo,
            "average_rating": rating["average_rating"],
        })

    return {"products": products, "recipes": recipes, "stores": stores_out}