from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.saving import Saving
from app.schemas.saving import SavingCreate, SavingUpdate


def create_saving(db: Session, saving: SavingCreate, user_id: str) -> Saving:
    db_saving = Saving(
        nama=saving.nama,
        target=saving.target,
        tersimpan=saving.tersimpan,
        deadline=saving.deadline,
        user_id=user_id,
    )
    db.add(db_saving)
    db.commit()
    db.refresh(db_saving)
    return db_saving


def get_user_savings(db: Session, user_id: str, skip: str = 0, limit: str = 100) -> List[Saving]:
    return (
        db.query(Saving)
        .filter(Saving.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_saving(db: Session, saving_id: str, user_id: str) -> Optional[Saving]:
    return (
        db.query(Saving)
        .filter(Saving.id == saving_id, Saving.user_id == user_id)
        .first()
    )


def update_saving(
    db: Session,
    saving_id: str,
    saving: SavingUpdate,
    user_id: str,
) -> Optional[Saving]:
    db_saving = get_user_saving(db, saving_id=saving_id, user_id=user_id)
    if not db_saving:
        return None

    update_data = saving.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_saving, key, value)

    db.commit()
    db.refresh(db_saving)
    return db_saving


def add_saving_funds(
    db: Session,
    saving_id: str,
    jumlah: float,
    user_id: str,
) -> Optional[Saving]:
    db_saving = get_user_saving(db, saving_id=saving_id, user_id=user_id)
    if not db_saving:
        return None

    db_saving.tersimpan += jumlah
    db.commit()
    db.refresh(db_saving)
    return db_saving


def delete_saving(db: Session, saving_id: str, user_id: str) -> bool:
    db_saving = get_user_saving(db, saving_id=saving_id, user_id=user_id)
    if not db_saving:
        return False

    db.delete(db_saving)
    db.commit()
    return True
