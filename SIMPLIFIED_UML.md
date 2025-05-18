# MLOps Hypervisor - Simplified UML Diagram

```
┌─────────────┐     ┌─────────────────┐     ┌───────────────┐
│    User     │     │  Organization   │     │    Cluster    │
├─────────────┤     ├─────────────────┤     ├───────────────┤
│ id          │     │ id              │     │ id            │
│ username    │     │ name            │     │ name          │
│ email       │     │ invite_code     │     │ total_ram     │
│ password    │     │ created_at      │     │ total_cpu     │
│ is_active   │     └────────┬────────┘     │ total_gpu     │
│ created_at  │              │              │ available_ram │
└──────┬──────┘              │              │ available_cpu │
       │                     │              │ available_gpu │
       │                     │              │ organization_id│
       │                     │              │ creator_id    │
       │                     │              │ created_at    │
       │                     │              └───────┬───────┘
       │                     │                      │
       │                     │                      │
       │   ┌────────────────────────────┐          │
       └───┤     user_organization      ├──────────┘
           ├────────────────────────────┤
           │ user_id                    │
           │ organization_id            │
           └────────────────────────────┘
                                                   ┌───────────────────┐
┌─────────────────────────┐                        │DeploymentStatus   │
│      Deployment         ├────────────────────────┤───────────────────┤
├─────────────────────────┤                        │ PENDING           │
│ id                      │                        │ RUNNING           │
│ name                    │                        │ COMPLETED         │
│ docker_image            │                        │ FAILED            │
│ status                  │                        │ CANCELLED         │
│ priority                │                        └───────────────────┘
│ required_ram            │
│ required_cpu            │                        ┌───────────────────┐
│ required_gpu            │                        │DeploymentPriority │
│ cluster_id              │                        ├───────────────────┤
│ user_id                 │                        │ LOW (1)           │
│ created_at              │                        │ MEDIUM (2)        │
│ started_at              │                        │ HIGH (3)          │
└────────────┬────────────┘                        └───────────────────┘
             │
             │
             │
┌────────────┴────────────┐
│  deployment_dependencies │
├─────────────────────────┤
│ dependent_id            │
│ dependency_id           │
└─────────────────────────┘


Relationships:
- User 1:N Deployments
- User 1:N Clusters (creator)
- User N:M Organizations
- Organization 1:N Clusters
- Cluster 1:N Deployments
- Deployment N:M Deployment (dependencies)
``` 