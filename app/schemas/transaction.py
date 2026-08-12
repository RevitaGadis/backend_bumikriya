from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

class TransactionType(str, Enum):
    income = "income"
    expense = "expense"

class TransactionBase(BaseModel):
    description: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    transaction_date: datetime = Field(default_factory=datetime.now)
    category: str = Field(..., max_length=50) # Still accept name from client
    transaction_type: TransactionType
    note: Optional[str] = Field(None, max_length=500)

class TransactionCreate(TransactionBase):
    pass

class TransactionInDBBase(TransactionBase):
    id: Optional[str] = None
    user_id: str
    category_id: str

    class Config:
        from_attributes = True

class Transaction(TransactionInDBBase):
    pass

class CategorySummary(BaseModel):
    category: str
    total_amount: float

class TransactionSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    expenses_by_category: List[CategorySummary]
