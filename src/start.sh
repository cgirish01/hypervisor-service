#!/bin/bash
set -e

# Initialize the database
echo "Initializing database..."
python -m src.utils.init_db

# Start the web application
echo "Starting web application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload 