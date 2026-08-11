from sqlalchemy.orm import Session
import secrets
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def get_user_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name).first()

def create_user(db: Session, user: UserCreate, role_name: str = "user"):
    hashed_password = get_password_hash(user.password)
    return create_user_with_password(db, name=user.name, email=user.email, hashed_password=hashed_password, role_name=role_name)

def create_user_with_password(db: Session, name: str, email: str, hashed_password: str, role_name: str = "user"):
    role = get_role_by_name(db, role_name)
    
    db_user = User(
        name=name, 
        email=email, 
        hashed_password=hashed_password,
        is_admin=role_name == "admin",
        role_id=role.id if role else None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_oauth_user(db: Session, email: str, name: str, role_name: str = "user"):
    random_password = secrets.token_urlsafe(32)
    hashed_password = get_password_hash(random_password)
    return create_user_with_password(db, name=name, email=email, hashed_password=hashed_password, role_name=role_name)

def update_password(db: Session, user: User, new_password: str):
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user
