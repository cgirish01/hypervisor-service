FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Make startup script executable
RUN chmod +x src/start.sh

# Expose port for the API
EXPOSE 8000

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
# Give ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Define environment variables with defaults (can be overridden at runtime)
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/hypervisor
ENV REDIS_URL=redis://redis:6379/0
ENV SECRET_KEY=changethisinproduction

# Command to run the application
CMD ["bash", "src/start.sh"] 