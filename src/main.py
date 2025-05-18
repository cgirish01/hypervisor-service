import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import logging

from src.models.base import Base, engine
from src.api.router import api_router
from src.scheduler.worker import start_scheduler, stop_scheduler

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="MLOps Hypervisor",
    description="A service that manages user authentication, organization membership, cluster resource allocation, and deployment scheduling.",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include API router
app.include_router(api_router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the application starts."""
    logger.info("Starting application")
    
    # Only start the scheduler if not in testing mode
    if os.environ.get("TESTING") != "true":
        start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the application shuts down."""
    logger.info("Shutting down application")
    
    # Only stop the scheduler if not in testing mode
    if os.environ.get("TESTING") != "true":
        stop_scheduler()


# Root endpoint - serve index.html
@app.get("/")
async def root():
    """Serve the index.html page."""
    return FileResponse("src/static/index.html")


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start the uvicorn server
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True) 