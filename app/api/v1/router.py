from fastapi import APIRouter
from app.api.v1.endpoints import users, auth

# Create main API router
api_router = APIRouter()

# Include routers from all endpoint modules
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Additional endpoints can be included here as they are developed
# api_router.include_router(games.router, prefix="/games", tags=["games"])
# api_router.include_router(stats.router, prefix="/stats", tags=["stats"])