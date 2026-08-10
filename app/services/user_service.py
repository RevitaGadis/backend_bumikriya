from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name).first()

def create_user(db: Session, user: UserCreate, role_name: str = "user"):
    hashed_password = get_password_hash(user.password)
    role = get_role_by_name(db, role_name)
    
    db_user = User(
        name=user.name, 
        email=user.email, 
        hashed_password=hashed_password,
        is_admin=role_name == "admin",
        role_id=role.id if role else None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
