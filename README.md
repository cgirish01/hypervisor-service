# MLOps Hypervisor Service

A backend service that manages user authentication, organization membership, cluster resource allocation, and deployment scheduling. The service optimizes for deployment priority, resource utilization, and maximizing successful deployments.

## Features

- **User Authentication and Organization Management**
  - Basic authentication (username and password)
  - Organization membership with invite codes
  - User management within organizations

- **Cluster Management**
  - Create clusters with fixed resources (RAM, CPU, GPU)
  - Track available and allocated resources

- **Deployment Management**
  - Create deployments with Docker images
  - Queue deployments when resources are unavailable
  - Preemption-based scheduling algorithm for high-priority deployments
  - Deployment dependency, 

- **Scheduling Algorithm**
  - Prioritizes high-priority deployments
  - Efficiently utilizes available resources
  - Maximizes successful deployments

## Technology Stack

- **Programming Language**: Python
- **Web Framework**: FastAPI
- **Database**: PostgreSQL
- **Task Queue**: Redis
- **Authentication**: JWT tokens
- **Containerization**: Docker & Docker Compose

## Project Structure

```
.
├── src/
│   ├── api/                  # API routes
│   ├── models/               # Database models
│   ├── scheduler/            # Deployment scheduler
│   ├── services/             # Business logic
│   ├── static/               # Static assets (CSS, JS)
│   ├── utils/                # Utilities
│   └── main.py               # Application entry point
├── tests/                    # Test files
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Multi-container Docker setup
├── .dockerignore             # Files excluded from Docker build
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup and Installation

### Docker Setup (Recommended)

1. Make sure you have Docker and Docker Compose installed:
```bash
docker --version
docker compose version
```

2. Create a `.env` file with appropriate configuration:
```
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/hypervisor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hypervisor

# Authentication
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis configuration
REDIS_URL=redis://redis:6379/0

# Scheduler configuration
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_INTERVAL=30

# Server configuration
PORT=8000
```

3. Build and start the containers:
```bash
docker compose build
docker compose up -d
```

4. Check the status of your containers:
```bash
docker compose ps
```

5. View logs:
```bash
docker compose logs -f web         # Web service logs
docker compose logs -f scheduler   # Scheduler service logs
docker compose logs -f worker      # Worker service logs
```

6. Stop the containers:
```bash
docker compose down        # Keep data volumes
docker compose down -v     # Remove data volumes (deletes all data)
```

The API will be available at `http://localhost:8000`. Swagger documentation is available at `http://localhost:8000/docs`.

### Local Development Setup

> **Note:** Due to multiple dependencies (PostgreSQL, Redis) and the need to run several components separately, local development setup can be time-consuming and complex. The Docker container method above is strongly recommended for most users.

1. Clone the repository:
```bash
git clone <repository-url>
cd mlops-hypervisor
```

2. Set up PostgreSQL database:
   - Install PostgreSQL if not already installed
   - Create a database named `hypervisor`
   - Create a user with appropriate permissions

3. Set up Redis:
   - Install Redis if not already installed
   - Start the Redis server

4. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

6. Create a `.env` file in the project root with the following variables:
```
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hypervisor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hypervisor

# Authentication
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (for scheduler)
REDIS_URL=redis://localhost:6379/0

# Scheduler configuration
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_INTERVAL=30

# Server configuration
PORT=8000
```

7. Run the main application:
```bash
python -m src.main
```

8. Run the scheduler (in a separate terminal):
```bash
python -m src.scheduler.run_scheduler
```

9. Run the worker (in a separate terminal):
```bash
python -m src.scheduler.worker
```

## Docker Architecture

The application is containerized using Docker Compose with the following services:

1. **Web**: FastAPI application serving the API
2. **DB**: PostgreSQL database for data persistence
3. **Redis**: In-memory data store for task queuing and caching
4. **Scheduler**: Background service running the scheduler at regular intervals
5. **Worker**: Service processing tasks from the Redis queue

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

## License

MIT License 