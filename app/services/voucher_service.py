from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.voucher import Voucher
from app.schemas.voucher import VoucherCreate, VoucherUpdate

def get_voucher(db: Session, voucher_id: str) -> Optional[Voucher]:
    return db.query(Voucher).filter(Voucher.id == voucher_id).first()

def get_voucher_by_code(db: Session, code: str) -> Optional[Voucher]:
    return db.query(Voucher).filter(Voucher.code == code).first()

def get_vouchers(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None, created_by: Optional[str] = None) -> List[Voucher]:
    query = db.query(Voucher)
    if is_active is not None:
        query = query.filter(Voucher.is_active == is_active)
    if created_by is not None:
        query = query.filter(Voucher.created_by == created_by)
    return query.order_by(Voucher.created_at.desc(), Voucher.id.desc()).offset(skip).limit(limit).all()

def get_vouchers_by_creator(db: Session, creator_id: str, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Voucher]:
    return get_vouchers(db, skip=skip, limit=limit, is_active=is_active, created_by=creator_id)

def create_voucher(db: Session, voucher: VoucherCreate, created_by: Optional[str] = None) -> Voucher:
    db_voucher = Voucher(
        code=voucher.code,
        name=voucher.name,
        description=voucher.description,
        discount_percent=voucher.discount_percent,
        max_discount=voucher.max_discount,
        min_purchase=voucher.min_purchase,
        quota=voucher.quota,
        is_active=voucher.is_active,
        valid_from=voucher.valid_from,
        valid_until=voucher.valid_until,
        created_by=created_by,
    )
    db.add(db_voucher)
    db.commit()
    db.refresh(db_voucher)
    return db_voucher

def update_voucher(db: Session, voucher_id: str, voucher: VoucherUpdate) -> Optional[Voucher]:
    db_voucher = get_voucher(db, voucher_id)
    if not db_voucher:
        return None

    update_data = voucher.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_voucher, key, value)

    db.add(db_voucher)
    db.commit()
    db.refresh(db_voucher)
    return db_voucher

def delete_voucher(db: Session, voucher_id: str) -> bool:
    db_voucher = get_voucher(db, voucher_id)
    if not db_voucher:
        return False
    db.delete(db_voucher)
    db.commit()
    return True