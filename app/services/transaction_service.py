from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionType

def create_transaction(db: Session, transaction: TransactionCreate, user_id: int):
    db_category = db.query(Category).filter(Category.name == transaction.category).first()
    if not db_category:
        raise HTTPException(status_code=400, detail=f"Category '{transaction.category}' does not exist.")

    db_transaction = Transaction(
        description=transaction.description,
        amount=transaction.amount,
        transaction_date=transaction.transaction_date,
        note=transaction.note,
        transaction_type=transaction.transaction_type,
        user_id=user_id,
        category_id=db_category.id
    )

    try:
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        setattr(db_transaction, 'category', db_category.name)
        return db_transaction
    except SQLAlchemyError:
        db.rollback()
        raise

def get_user_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.transaction_date.desc()).offset(skip).limit(limit).all()
    for t in transactions:
        setattr(t, 'category', t.category_rel.name)
    return transactions

def update_transaction(db: Session, transaction_id: int, transaction: TransactionCreate, user_id: int):
    db_transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()
    if not db_transaction:
        return None

    db_category = db.query(Category).filter(Category.name == transaction.category).first()
    if not db_category:
        raise HTTPException(status_code=400, detail=f"Category '{transaction.category}' does not exist.")

    db_transaction.description      = transaction.description
    db_transaction.amount           = transaction.amount
    db_transaction.transaction_date = transaction.transaction_date
    db_transaction.note             = transaction.note
    db_transaction.transaction_type = transaction.transaction_type
    db_transaction.category_id      = db_category.id

    try:
        db.commit()
        db.refresh(db_transaction)
        setattr(db_transaction, 'category', db_category.name)
        return db_transaction
    except SQLAlchemyError:
        db.rollback()
        raise

def delete_transaction(db: Session, transaction_id: int, user_id: int):
    db_transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()
    if not db_transaction:
        return False
    db.delete(db_transaction)
    db.commit()
    return True

def get_transaction_summary(db: Session, user_id: int):
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.income
    ).scalar() or 0.0

    total_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.expense
    ).scalar() or 0.0

    category_expenses = db.query(
        Category.name,
        func.sum(Transaction.amount).label("total_amount")
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.expense
    ).group_by(Category.name).all()

    expenses_by_category = [
        {"category": row[0], "total_amount": row[1]}
        for row in category_expenses
    ]

    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "balance": float(total_income - total_expense),
        "expenses_by_category": expenses_by_category
    }