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

## Project Structure

```
.
├── src/
│   ├── api/                  # API routes
│   ├── models/               # Database models
│   ├── scheduler/            # Deployment scheduler
│   ├── services/             # Business logic
│   ├── utils/                # Utilities
│   └── main.py               # Application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mlops-hypervisor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on the environment variables below:
```
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hypervisor

# Authentication
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (for scheduler)
REDIS_URL=redis://localhost:6379/0

# Scheduler configuration
SCHEDULER_INTERVAL=30  # seconds

# Server configuration
PORT=8000
```

5. Run the application:
```bash
python -m src.main
```

The API will be available at `http://localhost:8000`. Swagger documentation is available at `http://localhost:8000/docs`.

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

1. Runs at regular intervals (configurable)
2. Checks for pending deployments
3. Allocates resources based on priority
4. Handles preemption of lower-priority deployments when necessary

## License

MIT License 