from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.schemas import Deployment, DeploymentCreate, DeploymentUpdate, User
from src.models.models import DeploymentStatus
from src.services import deployment as deployment_service
from src.services import cluster as cluster_service
from src.services import organization as org_service
from src.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/deployments",
    tags=["deployments"],
)


@router.get("/", response_model=List[Deployment])
def get_deployments(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all deployments for the current user."""
    return deployment_service.get_user_deployments(db, current_user.id)[skip:skip+limit]


@router.post("/", response_model=Deployment)
def create_deployment(
    deployment: DeploymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new deployment for a cluster."""
    # First check if the cluster exists
    db_cluster = cluster_service.get_cluster(db, deployment.cluster_id)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Check if the user is a member of the organization that owns this cluster
    user_orgs = org_service.get_user_organizations(db, current_user.id)
    user_org_ids = [org.id for org in user_orgs]
    
    if db_cluster.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Not authorized to create a deployment for this cluster")
    
    # Validate dependencies
    if deployment.dependency_ids:
        for dep_id in deployment.dependency_ids:
            dependency = deployment_service.get_deployment(db, dep_id)
            if not dependency:
                raise HTTPException(status_code=404, detail=f"Dependency deployment with ID {dep_id} not found")
            
            # Check if the dependency is in the same cluster
            if dependency.cluster_id != deployment.cluster_id:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Dependency deployment with ID {dep_id} is not in the same cluster"
                )
    
    # Create the deployment
    db_deployment = deployment_service.create_deployment(db, deployment, current_user.id)
    if db_deployment is None:
        raise HTTPException(status_code=400, detail="Could not create deployment")
    
    return db_deployment


@router.get("/{deployment_id}", response_model=Deployment)
def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if this is the user's deployment
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    
    return db_deployment


@router.put("/{deployment_id}", response_model=Deployment)
def update_deployment(
    deployment_id: int,
    deployment: DeploymentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if this is the user's deployment
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to update this deployment")
    
    # Validate dependencies if provided
    if deployment.dependency_ids is not None:
        for dep_id in deployment.dependency_ids:
            # Prevent circular dependencies
            if dep_id == deployment_id:
                raise HTTPException(
                    status_code=400,
                    detail="A deployment cannot depend on itself"
                )
                
            dependency = deployment_service.get_deployment(db, dep_id)
            if not dependency:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dependency deployment with ID {dep_id} not found"
                )
            
            # Check if the dependency is in the same cluster
            if dependency.cluster_id != db_deployment.cluster_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dependency deployment with ID {dep_id} is not in the same cluster"
                )
                
            # Check for circular dependencies
            if is_circular_dependency(db, dep_id, deployment_id):
                raise HTTPException(
                    status_code=400,
                    detail="Circular dependency detected"
                )
    
    # Update the deployment
    updated_deployment = deployment_service.update_deployment(db, deployment_id, deployment)
    if updated_deployment is None:
        raise HTTPException(status_code=400, detail="Could not update deployment")
    
    return updated_deployment


def is_circular_dependency(db: Session, dep_id: int, deployment_id: int, visited=None):
    """Check if adding a dependency would create a circular dependency."""
    if visited is None:
        visited = set()
    
    if dep_id in visited:
        return False
    
    visited.add(dep_id)
    
    dependency = deployment_service.get_deployment(db, dep_id)
    if not dependency:
        return False
    
    for dep in dependency.dependencies:
        if dep.id == deployment_id:
            return True
        if is_circular_dependency(db, dep.id, deployment_id, visited):
            return True
    
    return False


@router.delete("/{deployment_id}", response_model=bool)
def delete_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if this is the user's deployment
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to delete this deployment")
    
    # Delete the deployment
    result = deployment_service.delete_deployment(db, deployment_id)
    if not result:
        raise HTTPException(status_code=400, detail="Could not delete deployment")
    
    return result


@router.post("/{deployment_id}/start", response_model=Deployment)
def start_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if this is the user's deployment
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to start this deployment")
    
    # Start the deployment
    started_deployment = deployment_service.start_deployment(db, deployment_id)
    if started_deployment is None:
        raise HTTPException(
            status_code=400, 
            detail="Could not start deployment. It may not be in a pending state or resources are unavailable."
        )
    
    return started_deployment


@router.post("/{deployment_id}/stop", response_model=Deployment)
def stop_deployment(
    deployment_id: int,
    status: DeploymentStatus = DeploymentStatus.COMPLETED,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stop a deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if this is the user's deployment
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to stop this deployment")
    
    # Stop the deployment
    stopped_deployment = deployment_service.stop_deployment(db, deployment_id, status)
    if stopped_deployment is None:
        raise HTTPException(
            status_code=400, 
            detail="Could not stop deployment. It may not be in a running state."
        )
    
    return stopped_deployment


@router.post("/{deployment_id}/cancel", response_model=Deployment)
def cancel_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if this is the user's deployment
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this deployment")
    
    # Cancel the deployment
    cancelled_deployment = deployment_service.cancel_deployment(db, deployment_id)
    if cancelled_deployment is None:
        raise HTTPException(
            status_code=400, 
            detail="Could not cancel deployment. It may not be in a pending state."
        )
    
    return cancelled_deployment


@router.get("/{deployment_id}/dependencies", response_model=List[Deployment])
def get_deployment_dependencies(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all dependencies for a deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Authorization checks
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    
    return db_deployment.dependencies


@router.get("/{deployment_id}/dependents", response_model=List[Deployment])
def get_deployment_dependents(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all deployments that depend on this deployment."""
    # Get the deployment
    db_deployment = deployment_service.get_deployment(db, deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Authorization checks
    if db_deployment.user_id != current_user.id:
        # If not, check if the user is a member of the organization that owns the cluster
        db_cluster = cluster_service.get_cluster(db, db_deployment.cluster_id)
        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        user_orgs = org_service.get_user_organizations(db, current_user.id)
        user_org_ids = [org.id for org in user_orgs]
        
        if db_cluster.organization_id not in user_org_ids:
            raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    
    return db_deployment.dependents 