from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DeploymentStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentPriorityEnum(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserJoinOrg(BaseModel):
    invite_code: str


class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class User(UserInDB):
    pass


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None


class OrganizationInDB(OrganizationBase):
    id: int
    invite_code: str
    created_at: datetime

    class Config:
        orm_mode = True


class Organization(OrganizationInDB):
    users: List[User] = []


# Cluster Schemas
class ClusterBase(BaseModel):
    name: str
    total_ram: float = Field(..., gt=0)
    total_cpu: float = Field(..., gt=0)
    total_gpu: float = Field(..., ge=0)


class ClusterCreate(ClusterBase):
    organization_id: int


class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    total_ram: Optional[float] = Field(None, gt=0)
    total_cpu: Optional[float] = Field(None, gt=0)
    total_gpu: Optional[float] = Field(None, ge=0)


class ClusterInDB(ClusterBase):
    id: int
    available_ram: float
    available_cpu: float
    available_gpu: float
    organization_id: int
    creator_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Cluster(ClusterInDB):
    pass


# Deployment Schemas
class DeploymentBase(BaseModel):
    name: str
    docker_image: str
    required_ram: float = Field(..., gt=0)
    required_cpu: float = Field(..., gt=0)
    required_gpu: float = Field(..., ge=0)
    priority: DeploymentPriorityEnum = DeploymentPriorityEnum.MEDIUM


class DeploymentCreate(DeploymentBase):
    cluster_id: int


class DeploymentUpdate(BaseModel):
    name: Optional[str] = None
    docker_image: Optional[str] = None
    required_ram: Optional[float] = Field(None, gt=0)
    required_cpu: Optional[float] = Field(None, gt=0)
    required_gpu: Optional[float] = Field(None, ge=0)
    priority: Optional[DeploymentPriorityEnum] = None
    status: Optional[DeploymentStatusEnum] = None


class DeploymentInDB(DeploymentBase):
    id: int
    status: DeploymentStatusEnum
    cluster_id: int
    user_id: int
    created_at: datetime
    started_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Deployment(DeploymentInDB):
    pass


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None 