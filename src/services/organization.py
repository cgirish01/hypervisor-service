from sqlalchemy.orm import Session
import uuid
import string
import random
from typing import List

from src.models.models import Organization, User
from src.models.schemas import OrganizationCreate, OrganizationUpdate


def generate_invite_code(length: int = 8):
    """Generate a random invite code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_organization(db: Session, org_id: int):
    """Get an organization by ID."""
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_organization_by_name(db: Session, name: str):
    """Get an organization by name."""
    return db.query(Organization).filter(Organization.name == name).first()


def get_organizations(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of organizations."""
    return db.query(Organization).offset(skip).limit(limit).all()


def get_user_organizations(db: Session, user_id: int):
    """Get organizations for a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    return user.organizations


def create_organization(db: Session, organization: OrganizationCreate, creator_id: int):
    """Create a new organization and add the creator as a member."""
    # Generate a unique invite code
    invite_code = generate_invite_code()
    while db.query(Organization).filter(Organization.invite_code == invite_code).first():
        invite_code = generate_invite_code()
    
    db_org = Organization(
        name=organization.name,
        invite_code=invite_code
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    
    # Add creator to organization
    creator = db.query(User).filter(User.id == creator_id).first()
    if creator:
        creator.organizations.append(db_org)
        db.commit()
    
    return db_org


def update_organization(db: Session, org_id: int, organization: OrganizationUpdate):
    """Update an organization."""
    db_org = get_organization(db, org_id)
    if not db_org:
        return None
    
    update_data = organization.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_org, key, value)
    
    db.commit()
    db.refresh(db_org)
    return db_org


def delete_organization(db: Session, org_id: int):
    """Delete an organization."""
    db_org = get_organization(db, org_id)
    if not db_org:
        return False
    
    db.delete(db_org)
    db.commit()
    return True


def regenerate_invite_code(db: Session, org_id: int):
    """Regenerate the invite code for an organization."""
    db_org = get_organization(db, org_id)
    if not db_org:
        return None
    
    # Generate a unique invite code
    invite_code = generate_invite_code()
    while db.query(Organization).filter(Organization.invite_code == invite_code).first():
        invite_code = generate_invite_code()
    
    db_org.invite_code = invite_code
    db.commit()
    db.refresh(db_org)
    return db_org 