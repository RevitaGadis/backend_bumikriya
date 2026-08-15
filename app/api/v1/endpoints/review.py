from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.services import review_service
from app.schemas.review import Review, ReviewCreate, ProductRatingSummary
from app.models.user import User

router = APIRouter()


@router.get("/products/{product_id}/reviews", response_model=List[Review])
def read_product_reviews(product_id: str, db: Session = Depends(deps.get_db)) -> Any:
    """List review sebuah produk. (Public)"""
    return review_service.get_reviews_by_product(db, product_id)


@router.get("/products/{product_id}/rating", response_model=ProductRatingSummary)
def read_product_rating(product_id: str, db: Session = Depends(deps.get_db)) -> Any:
    """Ringkasan rating produk (rata-rata + jumlah review). (Public)"""
    return review_service.get_product_rating_summary(db, product_id)


@router.post("/reviews", response_model=Review, status_code=201)
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Kasih review produk (harus sudah beli & pesanan selesai). (Buyer)"""
    return review_service.create_review(db, current_user.id, review_in)