from datetime import datetime
from typing import List, Optional
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

class RewardVoucherResponse(BaseModel):
    user_voucher_id: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    discount_percent: Optional[float] = 0
    min_purchase: Optional[float] = 0
    min_purchase_label: Optional[str] = None
    valid_until: Optional[datetime] = None
    is_claimed: Optional[bool] = False


class MembershipResponse(BaseModel):
    current_level: str
    current_level_code: str
    next_level: Optional[str] = None
    next_level_code: Optional[str] = None
    progress_percentage: int
    remaining_amount: int
    progress_text: str
    benefits: List[str] = []
    discount_percentage: float = 0
    reward_voucher: Optional[RewardVoucherResponse] = None

class OrderProductResponse(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    image: Optional[str] = None

class OrderInProfile(BaseModel):
    id: str
    order_number: str
    product: OrderProductResponse
    price: float
    status: str
    status_code: str
    action: Optional[str] = None
    created_at: Optional[datetime] = None

class UserProfile(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    is_admin: bool = False
    role_id: Optional[str] = None
    member_type: Optional[str] = None
    photoprofil: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    role: Optional[Role] = None
    membership: Optional[MembershipResponse] = None
    orders: List[OrderInProfile] = []

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
