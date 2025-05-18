from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Enum, Table, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

# Association table for many-to-many relationship between users and organizations
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("organization_id", Integer, ForeignKey("organizations.id"))
)

# Association table for deployment dependencies
deployment_dependencies = Table(
    "deployment_dependencies",
    Base.metadata,
    Column("dependent_id", Integer, ForeignKey("deployments.id"), primary_key=True),
    Column("dependency_id", Integer, ForeignKey("deployments.id"), primary_key=True)
)


class DeploymentStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentPriority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organizations = relationship("Organization", secondary=user_organization, back_populates="users")
    created_clusters = relationship("Cluster", back_populates="creator")
    deployments = relationship("Deployment", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    invite_code = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_organization, back_populates="organizations")
    clusters = relationship("Cluster", back_populates="organization")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    total_ram = Column(Float)  # in GB
    total_cpu = Column(Float)  # in cores
    total_gpu = Column(Float)  # in count
    
    available_ram = Column(Float)  # in GB
    available_cpu = Column(Float)  # in cores
    available_gpu = Column(Float)  # in count
    
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="clusters")
    creator = relationship("User", back_populates="created_clusters")
    deployments = relationship("Deployment", back_populates="cluster")


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    docker_image = Column(String)
    status = Column(Enum(DeploymentStatus), default=DeploymentStatus.PENDING)
    priority = Column(Enum(DeploymentPriority), default=DeploymentPriority.MEDIUM)
    
    required_ram = Column(Float)  # in GB
    required_cpu = Column(Float)  # in cores
    required_gpu = Column(Float)  # in count
    
    cluster_id = Column(Integer, ForeignKey("clusters.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    
    # Relationships
    cluster = relationship("Cluster", back_populates="deployments")
    user = relationship("User", back_populates="deployments")
    
    # Dependencies
    dependencies = relationship(
        "Deployment",
        secondary=deployment_dependencies,
        primaryjoin=(deployment_dependencies.c.dependent_id == id),
        secondaryjoin=(deployment_dependencies.c.dependency_id == id),
        backref="dependents"
    ) 