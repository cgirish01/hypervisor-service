# Docker Setup for MLOps Hypervisor

This README provides instructions for containerizing and running the MLOps Hypervisor application using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Files Overview

The Docker setup includes the following files:

- `Dockerfile`: Defines the container image for the application
- `docker-compose.yml`: Defines the services (web app, scheduler, database, and Redis)
- `.dockerignore`: Lists files and directories that should be excluded from the Docker build

## Services

The application consists of the following services:

1. **Web**: The FastAPI web application that serves the API
2. **DB**: PostgreSQL database for data persistence
3. **Redis**: In-memory data store used for task queuing and caching
4. **Scheduler**: Background service that runs the scheduler at regular intervals
5. **Worker**: Executes scheduled tasks from the Redis queue

## Configuration

Environment variables can be set in several ways:

1. In the `docker-compose.yml` file (default values are provided)
2. Using a `.env` file in the project root (not committed to version control)
3. Passing them when running `docker-compose up`

Important environment variables:

- `DATABASE_URL`: Connection string for the database
- `REDIS_URL`: Connection string for Redis
- `SECRET_KEY`: Secret key for authentication and security
- `SCHEDULER_INTERVAL_SECONDS`: How often the scheduler runs (default: 60 seconds)
- `SCHEDULER_INTERVAL`: How often the worker checks for tasks (default: 30 seconds)

## Running the Application

### Start the Application

```bash
# Build and start all services
docker-compose up -d

# To build images without caching
docker-compose build --no-cache

# To start only specific services
docker-compose up -d web db redis
```

### View Logs

```bash
# View logs from all services
docker-compose logs -f

# View logs from a specific service
docker-compose logs -f web
docker-compose logs -f scheduler
docker-compose logs -f worker
docker-compose logs -f redis
```

### Stop the Application

```bash
# Stop all services but keep volumes
docker-compose down

# Stop all services and remove volumes (deletes all data)
docker-compose down -v
```

## Database Migration

When running the application for the first time or after making database schema changes:

```bash
# Run Alembic migrations
docker-compose exec web alembic upgrade head
```

## Production Considerations

For production deployment:

1. Change default passwords and secrets
2. Use a separate database server with proper backups
3. Configure proper logging
4. Set up monitoring
5. Use Docker volumes for persistent data
6. Use a reverse proxy like Nginx for SSL termination
7. Consider using container orchestration like Kubernetes
8. Configure Redis persistence appropriately for your needs
9. Scale worker instances based on workload

## Backups

### Database Backups

```bash
# Backup PostgreSQL database
docker-compose exec db pg_dump -U postgres hypervisor > backup.sql

# Restore PostgreSQL database
cat backup.sql | docker-compose exec -T db psql -U postgres hypervisor
```

### Redis Backups

Redis is configured to save data to disk every 60 seconds if at least 1 key changed. The data is stored in the `redis_data` volume.

```bash
# Trigger a manual Redis backup
docker-compose exec redis redis-cli SAVE
```

## Troubleshooting

### Database Connection Issues

If the application cannot connect to the database:

1. Check if the PostgreSQL container is running: `docker-compose ps`
2. Check PostgreSQL logs: `docker-compose logs db`
3. Ensure the `DATABASE_URL` environment variable is correctly set

### Redis Connection Issues

If the application cannot connect to Redis:

1. Check if the Redis container is running: `docker-compose ps`
2. Check Redis logs: `docker-compose logs redis`
3. Ensure the `REDIS_URL` environment variable is correctly set

### Worker Issues

If tasks are not being processed:

1. Check worker logs: `docker-compose logs worker`
2. Verify Redis connection: `docker-compose exec redis redis-cli PING`
3. Check for errors in the worker implementation

### Application Errors

1. Check application logs: `docker-compose logs web`
2. Restart the application: `docker-compose restart web`

### Container Management

```bash
# List all running containers
docker-compose ps

# Restart a specific service
docker-compose restart web

# Execute a command in a running container
docker-compose exec web /bin/bash
``` 