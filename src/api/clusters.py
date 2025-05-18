from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.schemas import Cluster, ClusterCreate, ClusterUpdate, User
from src.services import cluster as cluster_service
from src.services import organization as org_service
from src.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/clusters",
    tags=["clusters"],
)


@router.get("/", response_model=List[Cluster])
def get_clusters(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all clusters that the current user has access to."""
    # Get all organizations the user is a member of
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    org_ids = [org.id for org in user_orgs]
    
    # Get all clusters for these organizations
    clusters = []
    for org_id in org_ids:
        org_clusters = cluster_service.get_organization_clusters(db, org_id)
        clusters.extend(org_clusters)
    
    return clusters[skip:skip+limit]


@router.post("/", response_model=Cluster)
def create_cluster(
    cluster: ClusterCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new cluster for an organization."""
    # Check if the user is a member of the organization
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if cluster.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    # Create the cluster
    return cluster_service.create_cluster(db, cluster, current_user.id)


@router.get("/{cluster_id}", response_model=Cluster)
def get_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific cluster."""
    # First get the cluster
    db_cluster = cluster_service.get_cluster(db, cluster_id)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Check if the user is a member of the organization that owns this cluster
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if db_cluster.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not authorized to access this cluster")
    
    return db_cluster


@router.put("/{cluster_id}", response_model=Cluster)
def update_cluster(
    cluster_id: int,
    cluster: ClusterUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a cluster."""
    # First get the cluster
    db_cluster = cluster_service.get_cluster(db, cluster_id)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Check if the user is a member of the organization that owns this cluster
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if db_cluster.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not authorized to update this cluster")
    
    # Update the cluster
    return cluster_service.update_cluster(db, cluster_id, cluster)


@router.delete("/{cluster_id}", response_model=bool)
def delete_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a cluster."""
    # First get the cluster
    db_cluster = cluster_service.get_cluster(db, cluster_id)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Check if the user is a member of the organization that owns this cluster
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if db_cluster.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not authorized to delete this cluster")
    
    # Delete the cluster
    return cluster_service.delete_cluster(db, cluster_id) 