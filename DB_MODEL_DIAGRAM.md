# MLOps Hypervisor Database Model

## Entities

### 1. User
- **id**: Integer (Primary Key)
- **username**: String (unique)
- **email**: String (unique)
- **hashed_password**: String
- **is_active**: Boolean
- **created_at**: DateTime
- **Relationships**:
  - Has many Deployments
  - Has many created Clusters
  - Belongs to many Organizations (through user_organization)

### 2. Organization
- **id**: Integer (Primary Key)
- **name**: String (unique)
- **invite_code**: String (unique)
- **created_at**: DateTime
- **Relationships**:
  - Has many Clusters
  - Has many Users (through user_organization)

### 3. Cluster
- **id**: Integer (Primary Key)
- **name**: String
- **total_ram**: Float
- **total_cpu**: Float
- **total_gpu**: Float
- **available_ram**: Float
- **available_cpu**: Float
- **available_gpu**: Float
- **organization_id**: Integer (Foreign Key to Organization)
- **creator_id**: Integer (Foreign Key to User)
- **created_at**: DateTime
- **Relationships**:
  - Belongs to one Organization
  - Belongs to one User (creator)
  - Has many Deployments

### 4. Deployment
- **id**: Integer (Primary Key)
- **name**: String
- **docker_image**: String
- **status**: DeploymentStatus (Enum)
- **priority**: DeploymentPriority (Enum)
- **required_ram**: Float
- **required_cpu**: Float
- **required_gpu**: Float
- **cluster_id**: Integer (Foreign Key to Cluster)
- **user_id**: Integer (Foreign Key to User)
- **created_at**: DateTime
- **started_at**: DateTime (nullable)
- **Relationships**:
  - Belongs to one Cluster
  - Belongs to one User
  - Has many dependencies (other Deployments through deployment_dependencies)
  - Is dependency for many other Deployments (through deployment_dependencies)

## Association Tables

### 1. user_organization
- **user_id**: Integer (Foreign Key to User)
- **organization_id**: Integer (Foreign Key to Organization)
- Links Users to Organizations in a many-to-many relationship

### 2. deployment_dependencies
- **dependent_id**: Integer (Foreign Key to Deployment, Primary Key)
- **dependency_id**: Integer (Foreign Key to Deployment, Primary Key)
- Links Deployments to other Deployments in a many-to-many relationship
- Represents dependencies between Deployments

## Enums

### 1. DeploymentStatus
- **PENDING**: Initial state of a deployment
- **RUNNING**: Deployment is currently running
- **COMPLETED**: Deployment has completed successfully
- **FAILED**: Deployment has failed
- **CANCELLED**: Deployment was cancelled before running

### 2. DeploymentPriority
- **LOW**: Priority level 1
- **MEDIUM**: Priority level 2
- **HIGH**: Priority level 3

## Relationships Overview

1. **Users and Organizations**: Many-to-Many relationship through user_organization table
   - A User can belong to multiple Organizations
   - An Organization can have multiple Users

2. **Users and Clusters**: One-to-Many relationship
   - A User can create multiple Clusters
   - A Cluster has one creator User

3. **Organizations and Clusters**: One-to-Many relationship
   - An Organization can have multiple Clusters
   - A Cluster belongs to one Organization

4. **Users and Deployments**: One-to-Many relationship
   - A User can create multiple Deployments
   - A Deployment is created by one User

5. **Clusters and Deployments**: One-to-Many relationship
   - A Cluster can have multiple Deployments
   - A Deployment belongs to one Cluster

6. **Deployments and Deployments**: Many-to-Many relationship through deployment_dependencies table
   - A Deployment can depend on multiple other Deployments
   - A Deployment can be a dependency for multiple other Deployments 