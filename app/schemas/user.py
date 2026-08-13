from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
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
    photoprofil: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[str] = None
    role_id: Optional[str] = None
    phone: Optional[str] = None
    member_type: Optional[str] = None
    photoprofil: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    role: Optional[Role] = None

class UserInDB(UserInDBBase):
    hashed_password: str

class MeResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

class ResetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=72)
    password_confirmation: str = Field(..., min_length=8, max_length=72)
    reset_token: Optional[str] = None

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Konfirmasi kata sandi tidak sesuai")
        return self
