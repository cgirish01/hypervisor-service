from fastapi import APIRouter

from src.api import auth, organizations, clusters, deployments

api_router = APIRouter()

# Include all API routers
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(clusters.router)
api_router.include_router(deployments.router) 