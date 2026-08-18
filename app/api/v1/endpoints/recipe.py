import json
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.services import recipe_service
from app.schemas.recipe import (
    RecipeSummary, RecipeDetail, RecipeCreate, RecipeUpdate,
    RecipeMaterialOut, RecipeMaterialCreate, ProductBrief,
)
from app.models.user import User
from app.core.uploads import save_upload

router = APIRouter()


@router.get("/", response_model=List[RecipeSummary])
def read_recipes(
    db: Session = Depends(deps.get_db),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return recipe_service.get_recipes(db, search, skip, limit)


@router.get("/{recipe_id}", response_model=RecipeDetail)
def read_recipe(recipe_id: str, db: Session = Depends(deps.get_db)) -> Any:
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
    *,
    db: Session = Depends(deps.get_db),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    materials: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    try:
        materials_list = json.loads(materials)
        material_in = [RecipeMaterialCreate(**m) for m in materials_list]
    except (json.JSONDecodeError, TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Field 'materials' harus berupa JSON array yang valid",
        )

    image_path = save_upload(image, subdir="recipes") if image else None
    data = RecipeCreate(
        title=title,
        description=description,
        category_id=category_id,
        image=image_path,
        materials=material_in,
    )
    recipe = recipe_service.create_recipe(db, data)
    return read_recipe(recipe.id, db)


@router.put("/{recipe_id}", response_model=RecipeDetail)
def update_recipe(
    recipe_id: str,
    *,
    db: Session = Depends(deps.get_db),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    materials: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    fields: dict = {}
    if title is not None:
        fields["title"] = title
    if description is not None:
        fields["description"] = description
    if category_id is not None:
        fields["category_id"] = category_id

    if materials is not None:
        try:
            materials_list = json.loads(materials)
            fields["materials"] = [RecipeMaterialCreate(**m) for m in materials_list]
        except (json.JSONDecodeError, TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Field 'materials' harus berupa JSON array yang valid",
            )

    if image is not None:
        fields["image"] = save_upload(image, subdir="recipes")

    recipe = recipe_service.update_recipe(db, recipe_id, RecipeUpdate(**fields))
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe tidak ditemukan")
    return read_recipe(recipe_id, db)


@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: str,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin),
) -> Any:
    deleted = recipe_service.delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe tidak ditemukan")
    return {"message": "Recipe dihapus berhasil"}