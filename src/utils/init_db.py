#!/usr/bin/env python3
"""
Database initialization script.
This script initializes the database schema using SQLAlchemy models.
"""
import logging
import os
import sys

# Add parent directory to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.base import Base, engine
from src.models.models import User, Organization, Cluster, Deployment
from src.models.models import user_organization, deployment_dependencies

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Creating database tables...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    init_db() 