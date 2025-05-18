from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.schemas import Organization, OrganizationCreate, OrganizationUpdate, User
from src.services import organization as org_service
from src.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


@router.get("/", response_model=List[Organization])
def get_organizations(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all organizations that the current user is a member of."""
    return org_service.get_user_organizations(db, current_user.id)


@router.post("/", response_model=Organization)
def create_organization(
    organization: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new organization with the current user as a member."""
    return org_service.create_organization(db, organization, current_user.id)


@router.get("/{org_id}", response_model=Organization)
def get_organization(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific organization."""
    # First check if the user is a member of this organization
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if org_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    db_org = org_service.get_organization(db, org_id)
    if db_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return db_org


@router.put("/{org_id}", response_model=Organization)
def update_organization(
    org_id: int,
    organization: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an organization."""
    # First check if the user is a member of this organization
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if org_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    db_org = org_service.update_organization(db, org_id, organization)
    if db_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return db_org


@router.delete("/{org_id}", response_model=bool)
def delete_organization(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an organization."""
    # First check if the user is a member of this organization
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if org_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    result = org_service.delete_organization(db, org_id)
    if not result:
        raise HTTPException(status_code=404, detail="Organization not found")
    return result


@router.post("/{org_id}/regenerate-invite", response_model=Organization)
def regenerate_invite_code(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate the invite code for an organization."""
    # First check if the user is a member of this organization
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if org_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    db_org = org_service.regenerate_invite_code(db, org_id)
    if db_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return db_org 