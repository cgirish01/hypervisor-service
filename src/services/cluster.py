from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.models import Cluster, Organization, User
from src.models.schemas import ClusterCreate, ClusterUpdate


def get_cluster(db: Session, cluster_id: int):
    """Get a cluster by ID."""
    return db.query(Cluster).filter(Cluster.id == cluster_id).first()


def get_clusters(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of clusters."""
    return db.query(Cluster).offset(skip).limit(limit).all()


def get_organization_clusters(db: Session, org_id: int):
    """Get clusters for a specific organization."""
    return db.query(Cluster).filter(Cluster.organization_id == org_id).all()


def create_cluster(db: Session, cluster: ClusterCreate, creator_id: int):
    """Create a new cluster."""
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == cluster.organization_id).first()
    if not org:
        return None
    
    # Create new cluster with initial available resources matching total resources
    db_cluster = Cluster(
        name=cluster.name,
        total_ram=cluster.total_ram,
        total_cpu=cluster.total_cpu,
        total_gpu=cluster.total_gpu,
        available_ram=cluster.total_ram,
        available_cpu=cluster.total_cpu,
        available_gpu=cluster.total_gpu,
        organization_id=cluster.organization_id,
        creator_id=creator_id
    )
    db.add(db_cluster)
    db.commit()
    db.refresh(db_cluster)
    return db_cluster


def update_cluster(db: Session, cluster_id: int, cluster: ClusterUpdate):
    """Update a cluster."""
    db_cluster = get_cluster(db, cluster_id)
    if not db_cluster:
        return None
    
    update_data = cluster.dict(exclude_unset=True)
    
    # If resources are being updated, update available resources accordingly
    if "total_ram" in update_data and update_data["total_ram"] > db_cluster.total_ram:
        diff = update_data["total_ram"] - db_cluster.total_ram
        db_cluster.available_ram += diff
    
    if "total_cpu" in update_data and update_data["total_cpu"] > db_cluster.total_cpu:
        diff = update_data["total_cpu"] - db_cluster.total_cpu
        db_cluster.available_cpu += diff
    
    if "total_gpu" in update_data and update_data["total_gpu"] > db_cluster.total_gpu:
        diff = update_data["total_gpu"] - db_cluster.total_gpu
        db_cluster.available_gpu += diff
    
    for key, value in update_data.items():
        setattr(db_cluster, key, value)
    
    db.commit()
    db.refresh(db_cluster)
    return db_cluster


def delete_cluster(db: Session, cluster_id: int):
    """Delete a cluster."""
    db_cluster = get_cluster(db, cluster_id)
    if not db_cluster:
        return False
    
    db.delete(db_cluster)
    db.commit()
    return True


def allocate_cluster_resources(db: Session, cluster_id: int, ram: float, cpu: float, gpu: float):
    """Allocate resources from a cluster for a deployment."""
    db_cluster = get_cluster(db, cluster_id)
    if not db_cluster:
        return False
    
    # Check if enough resources are available
    if (db_cluster.available_ram < ram or 
        db_cluster.available_cpu < cpu or 
        db_cluster.available_gpu < gpu):
        return False
    
    # Allocate resources
    db_cluster.available_ram -= ram
    db_cluster.available_cpu -= cpu
    db_cluster.available_gpu -= gpu
    
    db.commit()
    db.refresh(db_cluster)
    return True


def release_cluster_resources(db: Session, cluster_id: int, ram: float, cpu: float, gpu: float):
    """Release resources back to a cluster from a completed/failed deployment."""
    db_cluster = get_cluster(db, cluster_id)
    if not db_cluster:
        return False
    
    # Release resources
    db_cluster.available_ram += ram
    db_cluster.available_cpu += cpu
    db_cluster.available_gpu += gpu
    
    # Ensure we don't exceed total resources
    db_cluster.available_ram = min(db_cluster.available_ram, db_cluster.total_ram)
    db_cluster.available_cpu = min(db_cluster.available_cpu, db_cluster.total_cpu)
    db_cluster.available_gpu = min(db_cluster.available_gpu, db_cluster.total_gpu)
    
    db.commit()
    db.refresh(db_cluster)
    return True


def check_cluster_resources(db: Session, cluster_id: int, required_ram: float, required_cpu: float, required_gpu: float):
    """Check if a cluster has enough resources for a deployment."""
    db_cluster = get_cluster(db, cluster_id)
    if not db_cluster:
        return False
    
    return (db_cluster.available_ram >= required_ram and 
            db_cluster.available_cpu >= required_cpu and 
            db_cluster.available_gpu >= required_gpu) 