from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.saving import Saving, SavingAddDana, SavingCreate, SavingUpdate
from app.services import saving_service

router = APIRouter()


@router.post("/", response_model=Saving)
def create_saving(
    saving_in: SavingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return saving_service.create_saving(
        db=db,
        saving=saving_in,
        user_id=current_user.id,
    )


@router.get("/", response_model=List[Saving])
def read_savings(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return saving_service.get_user_savings(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=Saving)
def read_saving(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    saving = saving_service.get_user_saving(
        db=db,
        saving_id=id,
        user_id=current_user.id,
    )
    if not saving:
        raise HTTPException(status_code=404, detail="Saving not found")
    return saving


@router.put("/{id}", response_model=Saving)
def update_saving(
    id: int,
    saving_in: SavingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    saving = saving_service.update_saving(
        db=db,
        saving_id=id,
        saving=saving_in,
        user_id=current_user.id,
    )
    if not saving:
        raise HTTPException(status_code=404, detail="Saving not found")
    return saving


@router.patch("/{id}/add-dana", response_model=Saving)
def add_saving_funds(
    id: int,
    body: SavingAddDana,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    saving = saving_service.add_saving_funds(
        db=db,
        saving_id=id,
        jumlah=body.jumlah,
        user_id=current_user.id,
    )
    if not saving:
        raise HTTPException(status_code=404, detail="Saving not found")
    return saving


@router.delete("/{id}")
def delete_saving(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    ok = saving_service.delete_saving(
        db=db,
        saving_id=id,
        user_id=current_user.id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Saving not found")
    return {"message": "Saving berhasil dihapus"}
