from typing import List, Dict, Optional, Set, Tuple
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.models import Deployment, DeploymentStatus, DeploymentPriority
from src.services import deployment as deployment_service
from src.services import cluster as cluster_service

# Set up logging
logger = logging.getLogger(__name__)


class DeploymentScheduler:
    """
    Scheduler for handling deployment allocation and preemption.
    
    The scheduler optimizes for:
    1. Priority - Higher priority deployments are scheduled first
    2. Resource utilization - Efficiently use available resources
    3. Maximize successful deployments - Schedule as many deployments as possible
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def schedule_cluster_deployments(self, cluster_id: int) -> Dict[str, int]:
        """
        Schedule deployments for a specific cluster.
        Returns statistics about scheduling actions.
        """
        result = {
            "scheduled": 0,
            "preempted": 0,
            "unschedulable": 0
        }
        
        # Get the cluster
        cluster = cluster_service.get_cluster(self.db, cluster_id)
        if not cluster:
            logger.error(f"Cluster with ID {cluster_id} not found")
            return result
        
        # Get all pending deployments for this cluster, ordered by priority (high to low)
        pending_deployments = deployment_service.get_pending_deployments(self.db, cluster_id)
        
        # If no pending deployments, nothing to do
        if not pending_deployments:
            return result
        
        # First try to schedule deployments without preemption
        for deployment in pending_deployments:
            # Check if resources are available
            if cluster_service.check_cluster_resources(
                self.db, 
                cluster_id, 
                deployment.required_ram, 
                deployment.required_cpu, 
                deployment.required_gpu
            ):
                # Start the deployment
                if deployment_service.start_deployment(self.db, deployment.id):
                    result["scheduled"] += 1
        
        # If there are still pending deployments, try preemption for high priority ones
        remaining_pending = [d for d in pending_deployments if d.status == DeploymentStatus.PENDING]
        if not remaining_pending:
            return result
        
        # Get all running deployments with lower priority than our highest pending
        highest_pending_priority_value = max([d.priority.value for d in remaining_pending])
        running_deployments = self.db.query(Deployment).filter(
            Deployment.cluster_id == cluster_id,
            Deployment.status == DeploymentStatus.RUNNING,
        ).all()
        
        # Filter running deployments with lower priority manually
        running_deployments = [d for d in running_deployments if d.priority.value < highest_pending_priority_value]
        
        # Sort by priority value
        running_deployments.sort(key=lambda d: d.priority.value)
        
        # Try preemption
        if running_deployments and any(d.priority == DeploymentPriority.HIGH for d in remaining_pending):
            # Sort pending deployments by priority (high to low)
            high_priority_pending = [d for d in remaining_pending if d.priority == DeploymentPriority.HIGH]
            
            for pending_deployment in high_priority_pending:
                # If we can schedule directly, do it
                if deployment_service.start_deployment(self.db, pending_deployment.id):
                    result["scheduled"] += 1
                    continue
                
                # Try preemption
                preempted = self._try_preemption(
                    pending_deployment, 
                    running_deployments
                )
                
                if preempted:
                    # After preemption, try to start the deployment
                    if deployment_service.start_deployment(self.db, pending_deployment.id):
                        result["scheduled"] += 1
                        result["preempted"] += len(preempted)
                    else:
                        # This shouldn't happen if preemption was successful
                        logger.error(f"Failed to start deployment {pending_deployment.id} after preemption")
                        result["unschedulable"] += 1
                else:
                    result["unschedulable"] += 1
        
        # Count remaining unschedulable deployments
        result["unschedulable"] += len([
            d for d in pending_deployments 
            if d.status == DeploymentStatus.PENDING
        ])
        
        return result
    
    def _try_preemption(
        self, 
        pending_deployment: Deployment, 
        running_deployments: List[Deployment]
    ) -> List[int]:
        """
        Try to preempt running deployments to make room for a high-priority deployment.
        Returns a list of preempted deployment IDs.
        """
        # Sort running deployments by priority (low to high)
        sorted_running = sorted(running_deployments, key=lambda d: (d.priority.value, d.started_at or datetime.min))
        
        # Resources needed
        required_ram = pending_deployment.required_ram
        required_cpu = pending_deployment.required_cpu
        required_gpu = pending_deployment.required_gpu
        
        # Get the cluster's available resources
        cluster = cluster_service.get_cluster(self.db, pending_deployment.cluster_id)
        available_ram = cluster.available_ram
        available_cpu = cluster.available_cpu
        available_gpu = cluster.available_gpu
        
        # Calculate how much more resources we need
        needed_ram = max(0, required_ram - available_ram)
        needed_cpu = max(0, required_cpu - available_cpu)
        needed_gpu = max(0, required_gpu - available_gpu)
        
        # If no additional resources needed, no preemption needed
        if needed_ram <= 0 and needed_cpu <= 0 and needed_gpu <= 0:
            return []
        
        # Deployments to preempt
        to_preempt = []
        preempted_ram = 0
        preempted_cpu = 0
        preempted_gpu = 0
        
        # Try to preempt deployments until we have enough resources
        for deployment in sorted_running:
            # Skip if this deployment has higher or equal priority
            if deployment.priority.value >= pending_deployment.priority.value:
                continue
                
            to_preempt.append(deployment.id)
            preempted_ram += deployment.required_ram
            preempted_cpu += deployment.required_cpu
            preempted_gpu += deployment.required_gpu
            
            # Check if we have enough resources now
            if (preempted_ram >= needed_ram and 
                preempted_cpu >= needed_cpu and 
                preempted_gpu >= needed_gpu):
                break
        
        # If we can't get enough resources through preemption, don't preempt anything
        if (preempted_ram < needed_ram or 
            preempted_cpu < needed_cpu or 
            preempted_gpu < needed_gpu):
            return []
        
        # Stop the deployments to preempt
        for deployment_id in to_preempt:
            deployment_service.stop_deployment(self.db, deployment_id, DeploymentStatus.FAILED)
            
        return to_preempt
    
    def schedule_all_clusters(self) -> Dict[int, Dict[str, int]]:
        """
        Schedule deployments for all clusters.
        Returns statistics about scheduling actions per cluster.
        """
        result = {}
        
        # Get all clusters
        clusters = cluster_service.get_clusters(self.db)
        
        # Schedule deployments for each cluster
        for cluster in clusters:
            result[cluster.id] = self.schedule_cluster_deployments(cluster.id)
            
        return result 