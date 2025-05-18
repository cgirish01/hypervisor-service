from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.models.models import Deployment, DeploymentStatus, DeploymentPriority, Cluster, User
from src.models.schemas import DeploymentCreate, DeploymentUpdate, DeploymentPriorityEnum
from src.services import cluster as cluster_service


# Helper function to map between schema enum and model enum
def map_priority_enum(priority_enum: DeploymentPriorityEnum) -> DeploymentPriority:
    """Convert schema priority enum to database model priority enum."""
    if priority_enum == DeploymentPriorityEnum.LOW:
        return DeploymentPriority.LOW
    elif priority_enum == DeploymentPriorityEnum.MEDIUM:
        return DeploymentPriority.MEDIUM
    elif priority_enum == DeploymentPriorityEnum.HIGH:
        return DeploymentPriority.HIGH
    return DeploymentPriority.MEDIUM  # Default


def get_deployment(db: Session, deployment_id: int):
    """Get a deployment by ID."""
    return db.query(Deployment).filter(Deployment.id == deployment_id).first()


def get_deployments(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of deployments."""
    return db.query(Deployment).offset(skip).limit(limit).all()


def get_cluster_deployments(db: Session, cluster_id: int):
    """Get deployments for a specific cluster."""
    return db.query(Deployment).filter(Deployment.cluster_id == cluster_id).all()


def get_user_deployments(db: Session, user_id: int):
    """Get deployments for a specific user."""
    return db.query(Deployment).filter(Deployment.user_id == user_id).all()


def get_pending_deployments(db: Session, cluster_id: Optional[int] = None):
    """Get all pending deployments for a cluster, ordered by priority (high to low)."""
    query = db.query(Deployment).filter(Deployment.status == DeploymentStatus.PENDING)
    if cluster_id:
        query = query.filter(Deployment.cluster_id == cluster_id)
    return query.order_by(Deployment.priority.desc(), Deployment.created_at).all()


def create_deployment(db: Session, deployment: DeploymentCreate, user_id: int):
    """Create a new deployment."""
    # Check if the cluster exists
    db_cluster = db.query(Cluster).filter(Cluster.id == deployment.cluster_id).first()
    if not db_cluster:
        return None
    
    # Create the deployment (initially in pending state)
    db_deployment = Deployment(
        name=deployment.name,
        docker_image=deployment.docker_image,
        required_ram=deployment.required_ram,
        required_cpu=deployment.required_cpu,
        required_gpu=deployment.required_gpu,
        priority=map_priority_enum(deployment.priority),  # Convert the enum
        status=DeploymentStatus.PENDING,
        cluster_id=deployment.cluster_id,
        user_id=user_id
    )
    db.add(db_deployment)
    db.flush()  # Flush to get the deployment ID
    
    # Add dependencies
    if deployment.dependency_ids:
        for dep_id in deployment.dependency_ids:
            # Check if the dependency exists
            dependency = db.query(Deployment).filter(Deployment.id == dep_id).first()
            if dependency:
                db_deployment.dependencies.append(dependency)
    
    db.commit()
    db.refresh(db_deployment)
    
    return db_deployment


def update_deployment(db: Session, deployment_id: int, deployment: DeploymentUpdate):
    """Update a deployment."""
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment:
        return None
    
    # Store the original status and resource requirements
    original_status = db_deployment.status
    original_ram = db_deployment.required_ram
    original_cpu = db_deployment.required_cpu
    original_gpu = db_deployment.required_gpu
    
    # Update deployment fields
    update_data = deployment.dict(exclude_unset=True)
    
    # Handle priority enum conversion
    if 'priority' in update_data and update_data['priority'] is not None:
        update_data['priority'] = map_priority_enum(update_data['priority'])
    
    # Handle dependencies if provided
    if 'dependency_ids' in update_data and update_data['dependency_ids'] is not None:
        # Clear current dependencies
        db_deployment.dependencies = []
        
        # Add new dependencies
        for dep_id in update_data['dependency_ids']:
            dependency = db.query(Deployment).filter(Deployment.id == dep_id).first()
            if dependency:
                db_deployment.dependencies.append(dependency)
        
        # Remove from update_data to avoid setAttribute error
        del update_data['dependency_ids']
    
    for key, value in update_data.items():
        setattr(db_deployment, key, value)
    
    # Handle resource allocation/release if status changed
    if original_status != db_deployment.status:
        if original_status == DeploymentStatus.RUNNING and db_deployment.status != DeploymentStatus.RUNNING:
            # Release resources when a deployment is stopped
            cluster_service.release_cluster_resources(
                db, 
                db_deployment.cluster_id, 
                original_ram, 
                original_cpu, 
                original_gpu
            )
        
        elif original_status != DeploymentStatus.RUNNING and db_deployment.status == DeploymentStatus.RUNNING:
            # Allocate resources when a deployment is started
            if not cluster_service.allocate_cluster_resources(
                db, 
                db_deployment.cluster_id, 
                db_deployment.required_ram, 
                db_deployment.required_cpu, 
                db_deployment.required_gpu
            ):
                # If resources can't be allocated, revert status to original
                db_deployment.status = original_status
    
    # If just the resource requirements changed and deployment is running, 
    # we would need to release old resources and allocate new ones
    elif db_deployment.status == DeploymentStatus.RUNNING and (
        original_ram != db_deployment.required_ram or 
        original_cpu != db_deployment.required_cpu or 
        original_gpu != db_deployment.required_gpu
    ):
        # Release old resources
        cluster_service.release_cluster_resources(
            db,
            db_deployment.cluster_id,
            original_ram,
            original_cpu,
            original_gpu
        )
        
        # Try to allocate new resources
        if not cluster_service.allocate_cluster_resources(
            db,
            db_deployment.cluster_id,
            db_deployment.required_ram,
            db_deployment.required_cpu,
            db_deployment.required_gpu
        ):
            # If resources can't be allocated, revert to original resources
            db_deployment.required_ram = original_ram
            db_deployment.required_cpu = original_cpu
            db_deployment.required_gpu = original_gpu
            
            # Re-allocate original resources
            cluster_service.allocate_cluster_resources(
                db,
                db_deployment.cluster_id,
                original_ram,
                original_cpu,
                original_gpu
            )
    
    # Update started_at if deployment is now running
    if original_status != DeploymentStatus.RUNNING and db_deployment.status == DeploymentStatus.RUNNING:
        db_deployment.started_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_deployment)
    return db_deployment


def delete_deployment(db: Session, deployment_id: int):
    """Delete a deployment."""
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment:
        return False
    
    # Release resources if the deployment was running
    if db_deployment.status == DeploymentStatus.RUNNING:
        cluster_service.release_cluster_resources(
            db,
            db_deployment.cluster_id,
            db_deployment.required_ram,
            db_deployment.required_cpu,
            db_deployment.required_gpu
        )
    
    db.delete(db_deployment)
    db.commit()
    return True


def start_deployment(db: Session, deployment_id: int):
    """Start a deployment (allocate resources and change status)."""
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment or db_deployment.status != DeploymentStatus.PENDING:
        return None
    
    # Check dependencies
    for dependency in db_deployment.dependencies:
        # If any dependency is not in COMPLETED status, can't start this deployment
        if dependency.status != DeploymentStatus.COMPLETED:
            return None
    
    # Try to allocate resources
    if cluster_service.allocate_cluster_resources(
        db,
        db_deployment.cluster_id,
        db_deployment.required_ram,
        db_deployment.required_cpu,
        db_deployment.required_gpu
    ):
        # If successful, update status and started_at time
        db_deployment.status = DeploymentStatus.RUNNING
        db_deployment.started_at = datetime.utcnow()
        db.commit()
        db.refresh(db_deployment)
        return db_deployment
    
    # If resources can't be allocated, leave in pending state
    return None


def stop_deployment(db: Session, deployment_id: int, status: DeploymentStatus = DeploymentStatus.COMPLETED):
    """Stop a deployment (release resources and change status)."""
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment or db_deployment.status != DeploymentStatus.RUNNING:
        return None
    
    # Release resources
    cluster_service.release_cluster_resources(
        db,
        db_deployment.cluster_id,
        db_deployment.required_ram,
        db_deployment.required_cpu,
        db_deployment.required_gpu
    )
    
    # Update status
    db_deployment.status = status
    db.commit()
    db.refresh(db_deployment)
    
    # Check if any dependent deployments can now start
    check_dependent_deployments(db, db_deployment.id)
    
    return db_deployment


def check_dependent_deployments(db: Session, completed_deployment_id: int):
    """Check if any deployments dependent on the completed deployment can now start."""
    db_deployment = get_deployment(db, completed_deployment_id)
    if not db_deployment or db_deployment.status != DeploymentStatus.COMPLETED:
        return
    
    # Get all deployments that depend on this one
    for dependent in db_deployment.dependents:
        if dependent.status == DeploymentStatus.PENDING:
            # Check if all dependencies are completed
            all_dependencies_completed = True
            for dependency in dependent.dependencies:
                if dependency.status != DeploymentStatus.COMPLETED:
                    all_dependencies_completed = False
                    break
            
            # If all dependencies are completed, try to start this deployment
            if all_dependencies_completed:
                start_deployment(db, dependent.id)


def cancel_deployment(db: Session, deployment_id: int):
    """Cancel a pending deployment."""
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment or db_deployment.status != DeploymentStatus.PENDING:
        return None
    
    db_deployment.status = DeploymentStatus.CANCELLED
    db.commit()
    db.refresh(db_deployment)
    return db_deployment 