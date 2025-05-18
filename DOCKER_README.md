# Docker Setup for MLOps Hypervisor

This guide provides detailed instructions for containerizing and running the MLOps Hypervisor application using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10.0+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0.0+)

## Configuration Files Overview

### Dockerfile

The `Dockerfile` defines the container image for the application:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x src/start.sh

# Add a non-root user for security
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# The actual command is specified in docker-compose.yml
```

### docker-compose.yml

The `docker-compose.yml` file defines multiple services:

```yaml
services:
  web:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./src:/app/src
    restart: always
    command: bash -c "chmod +x /app/src/start.sh && /app/src/start.sh"

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
    ports:
      - "5432:5432"
    restart: always

  redis:
    image: redis:7.0-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    restart: always
    command: redis-server --save 60 1 --loglevel warning

  scheduler:
    build: .
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - SCHEDULER_INTERVAL_SECONDS=${SCHEDULER_INTERVAL_SECONDS}
    command: python -m src.scheduler.run_scheduler
    restart: always

  worker:
    build: .
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - SCHEDULER_INTERVAL=${SCHEDULER_INTERVAL}
    command: python -m src.scheduler.worker
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### .env File

Create a `.env` file in the project root with the following variables:

```
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/hypervisor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hypervisor

# Authentication
SECRET_KEY=your_strong_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis configuration
REDIS_URL=redis://redis:6379/0

# Scheduler configuration
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_INTERVAL=30

# Server configuration
PORT=8000
```

## Detailed Setup Instructions

### Initial Setup

1. Clone the repository and navigate to the project root:
   ```bash
   git clone <repository-url>
   cd mlops-hypervisor
   ```

2. Create the `.env` file with your configuration values (see above).

3. Build the Docker images:
   ```bash
   docker compose build
   ```

4. Start all services:
   ```bash
   docker compose up -d
   ```

### Managing Containers

- **View running containers**:
  ```bash
  docker compose ps
  ```

- **View logs from all services**:
  ```bash
  docker compose logs -f
  ```

- **View logs from a specific service**:
  ```bash
  docker compose logs -f web
  docker compose logs -f scheduler
  docker compose logs -f worker
  ```

- **Stop all services**:
  ```bash
  docker compose down
  ```

- **Stop and remove volumes** (deletes all data):
  ```bash
  docker compose down -v
  ```

- **Restart a specific service**:
  ```bash
  docker compose restart web
  ```

- **Execute a command in a running container**:
  ```bash
  docker compose exec web /bin/bash
  docker compose exec db psql -U postgres hypervisor
  docker compose exec redis redis-cli
  ```

## Service Details

### 1. Web Service

The FastAPI web application that serves the API endpoints:

- **Port**: 8000 (accessible at http://localhost:8000)
- **Documentation**: Available at http://localhost:8000/docs
- **Volume Mount**: `./src:/app/src` for development convenience
- **Command**: Runs the start.sh script which starts the Uvicorn server

### 2. Database Service (PostgreSQL)

Stores all application data:

- **Port**: 5432
- **Default Credentials**: username `postgres`, password `postgres`
- **Database Name**: `hypervisor`
- **Volume**: `postgres_data` for data persistence

### 3. Redis Service

Used for task queuing and caching:

- **Port**: 6380 (mapped from internal 6379)
- **Persistence**: Configured to save data every 60 seconds if at least 1 key changed
- **Volume**: `redis_data` for data persistence

### 4. Scheduler Service

Background service that runs the deployment scheduler:

- **Interval**: Configurable via `SCHEDULER_INTERVAL_SECONDS` (default: 60 seconds)
- **Function**: Allocates resources to pending deployments based on priority

### 5. Worker Service

Processes tasks from the Redis queue:

- **Interval**: Configurable via `SCHEDULER_INTERVAL` (default: 30 seconds)
- **Function**: Executes scheduled tasks

## Database Management

### Inspecting the Database

```bash
docker compose exec db psql -U postgres -d hypervisor
```

### Database Backup

```bash
docker compose exec db pg_dump -U postgres hypervisor > backup.sql
```

### Database Restore

```bash
cat backup.sql | docker compose exec -T db psql -U postgres hypervisor
```

## Redis Management

### Connecting to Redis CLI

```bash
docker compose exec redis redis-cli
```

### Redis Commands

- Check if Redis is working: `docker compose exec redis redis-cli ping`
- Get all keys: `docker compose exec redis redis-cli keys "*"`
- Monitor Redis commands in real-time: `docker compose exec redis redis-cli monitor`
- Trigger a manual save: `docker compose exec redis redis-cli save`

## Troubleshooting

### Container Not Starting

1. Check logs for errors:
   ```bash
   docker compose logs [service-name]
   ```

2. Ensure the `.env` file exists and has all required variables.

3. Try rebuilding the containers:
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

### Database Connection Issues

1. Verify the database container is running:
   ```bash
   docker compose ps db
   ```

2. Check database logs:
   ```bash
   docker compose logs db
   ```

3. Ensure the `DATABASE_URL` environment variable is correctly set in `.env`.

### Redis Connection Issues

1. Verify the Redis container is running:
   ```bash
   docker compose ps redis
   ```

2. Check Redis logs:
   ```bash
   docker compose logs redis
   ```

3. Test Redis connectivity:
   ```bash
   docker compose exec redis redis-cli ping
   ```

### Web Application Errors

1. Check web application logs:
   ```bash
   docker compose logs web
   ```

2. Verify the port mapping is correct in docker-compose.yml.

3. Ensure all environment variables are properly set.

### Scheduler or Worker Issues

1. Check service logs:
   ```bash
   docker compose logs scheduler
   docker compose logs worker
   ```

2. Verify Redis connectivity.

3. Check database connectivity.

## Cleanup Commands

### Remove Unused Images

```bash
docker image prune -a
```

### Remove All Stopped Containers

```bash
docker container prune
```

### Remove All Unused Volumes

```bash
docker volume prune
```

### Complete System Cleanup

```bash
docker system prune --volumes
```

## Production Considerations

For production deployment:

1. Use a secure, randomly generated `SECRET_KEY`
2. Change default database credentials
3. Configure proper logging
4. Set up monitoring
5. Use Docker volumes with backup mechanisms
6. Use a reverse proxy (Nginx, Traefik) for SSL termination
7. Consider container orchestration with Kubernetes for larger deployments
8. Implement regular database backup procedures 