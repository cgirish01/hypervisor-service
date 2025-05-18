import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, Table, Column, ForeignKey, Integer, MetaData
from models.base import DATABASE_URL

def create_deployment_dependencies_table():
    """Create the deployment_dependencies table if it doesn't exist."""
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # Define the table
    deployment_dependencies = Table(
        "deployment_dependencies",
        metadata,
        Column("dependent_id", Integer, ForeignKey("deployments.id"), primary_key=True),
        Column("dependency_id", Integer, ForeignKey("deployments.id"), primary_key=True)
    )
    
    # Create the table
    metadata.create_all(engine, tables=[deployment_dependencies])
    print("Deployment dependencies table created successfully!")

if __name__ == "__main__":
    create_deployment_dependencies_table() 