import time
import threading
import logging
import redis
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from src.models.base import SessionLocal
from src.scheduler.scheduler import DeploymentScheduler

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection for task queue
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

# Scheduler configuration
SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", "30"))  # seconds


class SchedulerWorker:
    """Worker that runs the deployment scheduler at regular intervals."""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler worker thread."""
        if self.running:
            logger.warning("Scheduler worker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Scheduler worker started")
    
    def stop(self):
        """Stop the scheduler worker thread."""
        if not self.running:
            logger.warning("Scheduler worker is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        logger.info("Scheduler worker stopped")
    
    def _run_scheduler_loop(self):
        """Run the scheduler in a loop at regular intervals."""
        while self.running:
            try:
                # Create a new database session for this iteration
                db = SessionLocal()
                
                # Run the scheduler
                scheduler = DeploymentScheduler(db)
                start_time = time.time()
                results = scheduler.schedule_all_clusters()
                
                # Log results
                total_scheduled = sum(r["scheduled"] for r in results.values())
                total_preempted = sum(r["preempted"] for r in results.values())
                total_unschedulable = sum(r["unschedulable"] for r in results.values())
                
                logger.info(
                    f"Scheduler run completed in {time.time() - start_time:.2f}s. "
                    f"Scheduled: {total_scheduled}, "
                    f"Preempted: {total_preempted}, "
                    f"Unschedulable: {total_unschedulable}"
                )
                
                # Store results in Redis for monitoring
                redis_client.set(
                    "scheduler:last_run", 
                    json.dumps({
                        "timestamp": datetime.utcnow().isoformat(),
                        "results": results,
                        "totals": {
                            "scheduled": total_scheduled,
                            "preempted": total_preempted,
                            "unschedulable": total_unschedulable
                        }
                    })
                )
                
                # Close the database session
                db.close()
                
                # Sleep until next interval
                time.sleep(SCHEDULER_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}", exc_info=True)
                time.sleep(5)  # Sleep a bit before retrying


# Singleton instance
scheduler_worker = SchedulerWorker()


def start_scheduler():
    """Start the scheduler worker."""
    scheduler_worker.start()


def stop_scheduler():
    """Stop the scheduler worker."""
    scheduler_worker.stop()


if __name__ == "__main__":
    # If run directly, start the scheduler worker
    logger.info("Starting scheduler worker as standalone process")
    start_scheduler()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler worker")
        stop_scheduler() 