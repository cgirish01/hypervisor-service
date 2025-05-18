#!/usr/bin/env python3
"""
Main entry point for running the deployment scheduler as a service.
This file is used as the entry point for the scheduler Docker container.
"""

import logging
import time
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# Add parent directory to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.base import engine, SessionLocal
from src.scheduler.scheduler import DeploymentScheduler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def wait_for_db(max_retries=30, delay=2):
    """Wait for the database to be ready."""
    retries = 0
    while retries < max_retries:
        try:
            # Try to connect to the database
            with Session(engine) as session:
                session.execute(text("SELECT 1"))
                logger.info("Database connection established")
                return True
        except OperationalError as e:
            retries += 1
            logger.warning(f"Database not ready yet. Retry {retries}/{max_retries}: {e}")
            time.sleep(delay)
    
    logger.error(f"Failed to connect to database after {max_retries} retries")
    return False

def main():
    """Main function to run the scheduler continuously."""
    logger.info("Starting Deployment Scheduler service")
    
    # Wait for the database to be ready
    if not wait_for_db():
        logger.error("Could not connect to the database. Exiting.")
        return
    
    # Run scheduler in an infinite loop
    scheduler_interval = int(os.environ.get("SCHEDULER_INTERVAL_SECONDS", "60"))
    
    logger.info(f"Scheduler will run every {scheduler_interval} seconds")
    
    while True:
        try:
            logger.info("Running scheduler cycle")
            db = get_db()
            
            # Create scheduler and run it
            scheduler = DeploymentScheduler(db)
            results = scheduler.schedule_all_clusters()
            
            # Log results
            for cluster_id, stats in results.items():
                logger.info(f"Cluster {cluster_id} scheduling stats: {stats}")
            
            db.close()
            
        except Exception as e:
            logger.exception(f"Error in scheduler cycle: {e}")
        
        logger.info(f"Scheduler cycle completed. Sleeping for {scheduler_interval} seconds")
        time.sleep(scheduler_interval)

if __name__ == "__main__":
    main() 