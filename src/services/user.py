from sqlalchemy.orm import Session
import uuid
from typing import Optional

from src.models.models import User, Organization
from src.models.schemas import UserCreate, UserUpdate
from src.utils.auth import get_password_hash, verify_password


def get_user(db: Session, user_id: int):
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of users."""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate):
    """Update a user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    """Delete a user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user with username and password."""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def join_organization(db: Session, user_id: int, invite_code: str):
    """Add a user to an organization using an invite code."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_org = db.query(Organization).filter(Organization.invite_code == invite_code).first()
    if not db_org:
        return None
    
    # Check if user is already in organization
    if db_org in db_user.organizations:
        return db_org
    
    db_user.organizations.append(db_org)
    db.commit()
    db.refresh(db_user)
    return db_org 