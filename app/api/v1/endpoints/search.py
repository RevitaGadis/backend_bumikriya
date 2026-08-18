from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.recipe import ProductBrief, RecipeSummary
from app.services import search_service


router = APIRouter()


class StoreSearchResult(BaseModel):
    id: str
    store_name: str
    logo: Optional[str] = None
    average_rating: float = 0.0


class SearchAllResponse(BaseModel):
    products: List[ProductBrief]
    recipes: List[RecipeSummary]
    stores: List[StoreSearchResult]


@router.get("/all", response_model=SearchAllResponse)
def search_everything(
    q: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    return search_service.search_all(db, q)