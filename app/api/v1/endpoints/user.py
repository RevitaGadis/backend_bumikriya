from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from app.api import deps
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.services import dashboard_service
from app.schemas.user import User as UserSchema

router = APIRouter()

class ProfileUpdate(BaseModel):
    name:  Optional[str]      = None
    email: Optional[EmailStr] = None

class PasswordUpdate(BaseModel):
    password_lama: str = Field(..., min_length=1)
    password_baru: str = Field(..., min_length=8)

@router.get("/dashboard")
def read_user_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_regular_user)
) -> Any:
    return dashboard_service.get_user_dashboard(db, current_user)

@router.get("/me", response_model=UserSchema)
def get_profile(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return current_user

@router.put("/me", response_model=UserSchema)
def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if body.name:
        current_user.name = body.name
    if body.email:
        existing = db.query(User).filter(User.email == body.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah digunakan akun lain")
        current_user.email = body.email
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
def update_password(
    body: PasswordUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if not verify_password(body.password_lama, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password lama salah")
    current_user.hashed_password = get_password_hash(body.password_baru)
    db.commit()
    return {"message": "Password berhasil diubah"}
