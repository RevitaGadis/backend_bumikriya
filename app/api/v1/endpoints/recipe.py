from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.services import recipe_service
from app.schemas.recipe import RecipeSummary, RecipeDetail, RecipeCreate, RecipeUpdate, RecipeMaterialOut
from app.models.user import User
from app.schemas.recipe import RecipeSummary
from pydantic import BaseModel
from typing import List

router = APIRouter()


@router.get("/", response_model=List[RecipeSummary])
def read_recipes(
    db: Session = Depends(deps.get_db),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List/search recipe berdasarkan title. (Public)"""
    return recipe_service.get_recipes(db, search, skip, limit)


@router.get("/{recipe_id}", response_model=RecipeDetail)
def read_recipe(recipe_id: str, db: Session = Depends(deps.get_db)) -> Any:
    """Detail recipe + rekomendasi produk per bahan. (Public)"""
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe tidak ditemukan")

    materials_out = []
    for m in recipe.materials:
        recommended = recipe_service.get_recommended_products(
            db, m.category_id, exclude_id=m.suggested_product_id
        )
        materials_out.append(RecipeMaterialOut(
            id=m.id,
            material_name=m.material_name,
            quantity_needed=m.quantity_needed,
            unit=m.unit,
            note=m.note,
            suggested_product=m.suggested_product,
            recommended_products=recommended,
        ))

    return RecipeDetail(
        id=recipe.id, title=recipe.title, description=recipe.description,
        image=recipe.image, materials=materials_out,
    )


@router.post("/", response_model=RecipeDetail, status_code=201)
def create_recipe(
    data: RecipeCreate,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """Bikin recipe baru. (Admin only)"""
    recipe = recipe_service.create_recipe(db, data)
    return read_recipe(recipe.id, db)


@router.put("/{recipe_id}", response_model=RecipeDetail)
def update_recipe(
    recipe_id: str,
    data: RecipeUpdate,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """Update recipe. (Admin only)"""
    recipe = recipe_service.update_recipe(db, recipe_id, data)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe tidak ditemukan")
    return read_recipe(recipe_id, db)


@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: str,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    """Hapus recipe. (Admin only)"""
    deleted = recipe_service.delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe tidak ditemukan")
    return {"message": "Recipe deleted"}


class StoreSearchResult(BaseModel):
    id: str
    store_name: str
    logo: Optional[str] = None
    average_rating: float = 0.0

class SearchAllResponse(BaseModel):
    products: List[ProductBrief]
    recipes: List[RecipeSummary]
    stores: List[StoreSearchResult]


@router.get("/search/all", response_model=SearchAllResponse)
def search_everything(q: str, db: Session = Depends(deps.get_db)) -> Any:
    """Search bar utama — produk, recipe, dan toko sekaligus. (Public)"""
    return recipe_service.search_all(db, q)