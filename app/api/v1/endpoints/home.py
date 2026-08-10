from typing import Any
from fastapi import APIRouter, Depends
from app.models.user import User
from app.api import deps

router = APIRouter()

@router.get("/")
def read_root(current_user: User = Depends(deps.get_current_user)) -> Any:
    return {"message": f"Welcome, {current_user.email}! You are logged in."}
