# MLOps Hypervisor Service

A backend service for managing user authentication, organization membership, cluster resource allocation, and deployment scheduling. The service optimizes for deployment priority, resource utilization, and maximizing successful deployments.

---

## Quickstart

1. **Clone the repository and enter the directory:**
   ```bash
   git clone <repository-url>
   cd hypervisor-service
   ```
2. **Start the stack with Docker Compose:**
   ```bash
   docker compose build
   docker compose up -d
   ```
3. **Access the API:**
   - API: [http://localhost:8000](http://localhost:8000)
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

4. **Run the test suite:**
   ```bash
   pytest --maxfail=3 --disable-warnings -v tests/
   ```

---

## Features

### Authentication & Authorization
- **JWT-based authentication** (username and password login, JWT tokens for API access)
- Organization membership with invite codes
- User management within organizations

### Cluster & Resource Management
- Create clusters with fixed resources (RAM, CPU, GPU)
- Track available and allocated resources

### Deployment Management
- Create deployments with Docker images
- Queue deployments when resources are unavailable
- Preemption-based scheduling for high-priority deployments
- Deployment dependencies (auto-start when dependencies complete)

### Scheduling Algorithm
- Prioritizes high-priority deployments
- Efficiently utilizes available resources
- Maximizes successful deployments

---

## Technology Stack

- **Programming Language**: Python
- **Web Framework**: FastAPI
- **Database**: PostgreSQL
- **Task Queue**: Redis
- **Authentication**: JWT tokens
- **Containerization**: Docker & Docker Compose

---

## Project Structure

```
.
├── src/                # Application source code
│   ├── api/            # API routes
│   ├── models/         # Database models
│   ├── scheduler/      # Deployment scheduler
│   ├── services/       # Business logic
│   ├── static/         # Static assets (CSS, JS)
│   ├── utils/          # Utilities
│   └── main.py         # Application entry point
├── tests/              # Test files
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Multi-container Docker setup
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Setup and Installation

### Docker Setup (Recommended)

1. Ensure you have Docker and Docker Compose installed:
   ```bash
   docker --version
   docker compose version
   ```
2. Create a `.env` file with configuration (see below for example).
3. Build and start the containers:
   ```bash
   docker compose build
   docker compose up -d
   ```
4. Access the API at [http://localhost:8000](http://localhost:8000) and docs at [http://localhost:8000/docs](http://localhost:8000/docs).

#### Example .env file
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/hypervisor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hypervisor
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379/0
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_INTERVAL=30
PORT=8000
```

---

## API Authentication

- All protected endpoints require a JWT Bearer token in the `Authorization` header.
- Obtain a token via `POST /token` and use it in subsequent requests:

```bash
# Example: Login and use JWT token with curl
TOKEN=$(curl -s -X POST http://localhost:8000/token -d 'username=youruser&password=yourpass' | jq -r .access_token)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/organizations/
```

- Full interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Test Suite

> **Note:** Tests assume the API is running at `http://localhost:8000`.

You can run all tests using:

```bash
pytest --maxfail=3 --disable-warnings -v tests/
```

Or to run only deployment tests:

```bash
pytest --maxfail=3 --disable-warnings -v tests/test_deployment_api.py
```

### What the tests check

#### Authentication & Organization
- **Register and Login:** Ensures user registration and login works.
- **Join Organization:** Ensures users can join organizations via invite code.
- **Organization CRUD:** Create, get, update, list, delete, and regenerate invite code for organizations.

#### Cluster
- **Cluster CRUD:** Create, get, update, list, and delete clusters. Ensures resource tracking and cleanup.

#### Deployment
- **Create Deployment:** Can create a deployment with or without dependencies.
- **Get/Update/List/Delete Deployment:** Standard CRUD operations for deployments.
- **Start/Stop/Cancel Deployment:** Can start, stop, and cancel deployments, with correct state transitions.
- **Dependency Logic:**
    - **test_start_deployment_with_dependency:**
      - Ensures a deployment with a dependency cannot start until the dependency is completed.
      - After the dependency is completed, the dependent deployment is auto-started if resources are available.
    - **test_dependency_state_transitions:**
      - Checks that if dep1 depends on dep2:
        1. Both are initially pending.
        2. Starting dep2 does not start dep1 (dep1 remains pending).
        3. Completing dep2 causes dep1 to become running (auto-started by backend).
- **Dependency/Dependent Endpoints:**
    - Can fetch all dependencies and dependents for a deployment.

All tests clean up after themselves, deleting any created users, organizations, clusters, or deployments (where possible).

See the `tests/` directory for more details and to add your own tests.

---

## API Endpoints

- **Authentication**
  - `POST /register`: Register a new user
  - `POST /token`: Obtain access token (login)
  - `POST /join-organization`: Join an organization using an invite code

- **Organizations**
  - `GET /organizations`: List organizations
  - `POST /organizations`: Create a new organization
  - `GET /organizations/{org_id}`: Get organization details
  - `PUT /organizations/{org_id}`: Update an organization
  - `DELETE /organizations/{org_id}`: Delete an organization
  - `POST /organizations/{org_id}/regenerate-invite`: Regenerate invite code

- **Clusters**
  - `GET /clusters`: List clusters
  - `POST /clusters`: Create a new cluster
  - `GET /clusters/{cluster_id}`: Get cluster details
  - `PUT /clusters/{cluster_id}`: Update a cluster
  - `DELETE /clusters/{cluster_id}`: Delete a cluster

- **Deployments**
  - `GET /deployments`: List deployments
  - `POST /deployments`: Create a new deployment
  - `GET /deployments/{deployment_id}`: Get deployment details
  - `PUT /deployments/{deployment_id}`: Update a deployment
  - `DELETE /deployments/{deployment_id}`: Delete a deployment
  - `POST /deployments/{deployment_id}/start`: Start a deployment
  - `POST /deployments/{deployment_id}/stop`: Stop a deployment
  - `POST /deployments/{deployment_id}/cancel`: Cancel a pending deployment

---

## Scheduler

The system includes a background scheduler that:

1. Runs at regular intervals (configurable via `SCHEDULER_INTERVAL_SECONDS`)
2. Checks for pending deployments
3. Allocates resources based on priority
4. Handles preemption of lower-priority deployments when necessary

### Scheduling Algorithm

At its core, the scheduler follows a two-phase, priority-driven, resource-aware algorithm:

#### Phase 1: Non-preemptive scheduling

- Fetch pending deployments, sorted from highest to lowest priority.
- For each pending job, check if the cluster's currently free RAM/CPU/GPU can satisfy its requirements.
- If yes, start that deployment immediately (mark it RUNNING) and count it as "scheduled."

#### Phase 2: Preemptive scheduling for high-priority jobs

- If any HIGH-priority deployments remain PENDING after Phase 1, gather all RUNNING deployments on that cluster whose priority is strictly lower than the highest pending job.
- Sort those running jobs by (priority ascending, start-time ascending)—i.e. evict lowest-priority, oldest first.
- For each high-priority pending deployment:
  - Recheck whether it can fit in the now-free resources. If yes, start it.
  - Otherwise, accumulate resources by "preempting" (stopping) the sorted running jobs one by one until you've freed enough RAM/CPU/GPU.
  - After each preemption, retry starting the pending job. If it now fits, count it as "scheduled" and tally how many you preempted.
  - If you exhaust all lower-priority jobs and still can't fit, mark it "unschedulable."

#### Final accounting

- Any deployments still marked PENDING after both phases are counted as "unschedulable."
- The scheduler returns per-cluster totals:
  - scheduled = jobs successfully started
  - preempted = number of running jobs you evicted to make room
  - unschedulable = jobs still pending at the end

By splitting it into a "try without kicking anyone out" pass and then a "preempt if a high-priority job still can't fit" pass, the scheduler ensures maximum throughput while always giving precedence to the most critical deployments.

---

## Production Considerations

For production deployment:

1. Use strong, unique passwords and a secure `SECRET_KEY`
2. Configure secure database authentication
3. Set up proper logging and monitoring
4. Use Docker volumes for persistent data storage
5. Consider using a reverse proxy (Nginx/Traefik) for SSL termination
6. Implement a backup strategy for PostgreSQL
7. Enable Redis persistence for data reliability
8. Scale worker instances based on workload

---

## Troubleshooting

### Container Issues
- View logs: `docker compose logs -f [service-name]`
- Restart a service: `docker compose restart [service-name]` 
- Rebuild containers: `docker compose build --no-cache`

### Database Connection Issues
- Check database logs: `docker compose logs db`
- Ensure the `DATABASE_URL` environment variable is correct
- Verify database migrations have been applied

### Redis Connection Issues
- Check Redis logs: `docker compose logs redis`
- Verify the `REDIS_URL` environment variable is correct
- Test Redis connectivity: `docker compose exec redis redis-cli ping`

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