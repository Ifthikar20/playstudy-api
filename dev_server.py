"""
Lightweight development server for the PlayStudy API.
This uses mock endpoints and doesn't require DynamoDB or any real database.
"""

import os
import uvicorn
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, Field

# Setup environment
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "thisisasecretkey1234567890thisisasecretkey"

# Create models
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    image: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: datetime
    xp_points: int
    level: int
    games_played: int

class UpdateXPRequest(BaseModel):
    xp_increase: int = Field(..., gt=0)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Mock database
USERS = [
    {
        "id": "1",
        "email": "user@example.com",
        "name": "Test User",
        "image": None,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "last_login": datetime.utcnow(),
        "xp_points": 200,
        "level": 3,
        "games_played": 5
    }
]

# Create FastAPI app
app = FastAPI(
    title="PlayStudy.AI API - Development Version",
    description="Development API for PlayStudy.AI (Mock Version)",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
api_router = APIRouter(prefix="/api/v1")

# Auth endpoints
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/login", response_model=Token)
async def login(email: str = "user@example.com", password: str = "password"):
    """Login endpoint (mock)"""
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer"
    }

@auth_router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register endpoint (mock)"""
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "name": user_data.name,
        "image": user_data.image,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "last_login": datetime.utcnow(),
        "xp_points": 0,
        "level": 1,
        "games_played": 0
    }
    USERS.append(new_user)
    return new_user

# User endpoints
user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me", response_model=UserResponse)
async def get_current_user_profile():
    """Get current user profile (mock)"""
    return USERS[0]

@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID (mock)"""
    for user in USERS:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@user_router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Create a new user (mock)"""
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "name": user_data.name,
        "image": user_data.image,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "last_login": datetime.utcnow(),
        "xp_points": 0,
        "level": 1,
        "games_played": 0
    }
    USERS.append(new_user)
    return new_user

@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user profile (mock)"""
    for user in USERS:
        if user["id"] == user_id:
            if user_data.name is not None:
                user["name"] = user_data.name
            if user_data.image is not None:
                user["image"] = user_data.image
            user["updated_at"] = datetime.utcnow()
            return user
    raise HTTPException(status_code=404, detail="User not found")

@user_router.put("/{user_id}/xp", response_model=UserResponse)
async def update_user_xp(user_id: str, xp_data: UpdateXPRequest):
    """Update user XP points (mock)"""
    for user in USERS:
        if user["id"] == user_id:
            user["xp_points"] += xp_data.xp_increase
            user["level"] = min(max(1, int(user["xp_points"] / 100) + 1), 100)
            user["updated_at"] = datetime.utcnow()
            return user
    raise HTTPException(status_code=404, detail="User not found")

@user_router.put("/{user_id}/game-played", response_model=UserResponse)
async def increment_games_played(user_id: str):
    """Increment the games played counter for a user (mock)"""
    for user in USERS:
        if user["id"] == user_id:
            user["games_played"] += 1
            user["updated_at"] = datetime.utcnow()
            return user
    raise HTTPException(status_code=404, detail="User not found")

@user_router.get("/", response_model=Dict[str, Any])
async def list_users(limit: int = 100):
    """List users with pagination (mock)"""
    return {
        "items": USERS[:limit],
        "count": len(USERS),
        "last_evaluated_key": None
    }

# Add routers to API
api_router.include_router(auth_router)
api_router.include_router(user_router)

# Add API router to app
app.include_router(api_router)

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint for health checks"""
    return {"status": "online", "service": "PlayStudy.AI API (Dev)", "version": "0.1.0"}

@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting PlayStudy API in development mode (mock data)")
    print("API documentation: http://localhost:8080/docs")
    
    # Start the API
    uvicorn.run(
        "dev_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )