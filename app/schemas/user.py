from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.role import Role

class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_admin: Optional[bool] = False

class UserCreate(UserBase):
    password: str = Field(..., max_length=72)

class UserUpdate(UserBase):
    name: Optional[str] = None
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[str] = None
    role_id: Optional[str] = None
    phone: Optional[str] = None
    member_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    role: Optional[Role] = None

class UserInDB(UserInDBBase):
    hashed_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
