from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

class SavingBase(BaseModel):
    nama:     str   = Field(..., max_length=255)
    target:   float = Field(..., gt=0)
    tersimpan:float = Field(default=0, ge=0)
    deadline: Optional[date] = None

class SavingCreate(SavingBase):
    pass

class SavingUpdate(BaseModel):
    nama:     Optional[str]   = None
    target:   Optional[float] = None
    tersimpan:Optional[float] = None
    deadline: Optional[date]  = None

class SavingAddDana(BaseModel):
    jumlah: float = Field(..., gt=0)

class Saving(SavingBase):
    id:      int
    user_id: int

    class Config:
        from_attributes = True
