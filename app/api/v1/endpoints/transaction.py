from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services import transaction_service
from app.schemas.transaction import TransactionCreate, Transaction, TransactionSummary
from app.models.user import User

router = APIRouter()

@router.post("/transactions/", response_model=Transaction)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    transaction = transaction_service.create_transaction(db=db, transaction=transaction_in, user_id=current_user.id)
    return transaction

@router.get("/history", response_model=List[Transaction])
def read_transaction_history(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    transactions = transaction_service.get_user_transactions(db, user_id=current_user.id, skip=skip, limit=limit)
    return transactions

@router.get("/summary", response_model=TransactionSummary)
def read_transaction_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    summary = transaction_service.get_transaction_summary(db, user_id=current_user.id)
    return summary

@router.put("/transactions/{id}", response_model=Transaction)
def update_transaction(
    id: int,
    transaction_in: TransactionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    transaction = transaction_service.update_transaction(
        db=db, transaction_id=id, transaction=transaction_in, user_id=current_user.id
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.delete("/transactions/{id}")
def delete_transaction(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    ok = transaction_service.delete_transaction(db=db, transaction_id=id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaksi berhasil dihapus"}