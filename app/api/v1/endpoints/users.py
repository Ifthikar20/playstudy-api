from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from app.models.schemas.user import UserCreate, UserUpdate, UserResponse, UpdateXPRequest
from app.services.user_services import UserService
from app.core.exceptions import ResourceNotFoundException
from app.api.dependencies import get_user_service
import logging
import os

# Use development dependency in local mode
if os.environ.get("DEBUG") == "True":
    from app.api.dev_dependencies import get_test_user as get_current_user
else:
    from app.middleware.authentication import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get current user profile"""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get user by ID"""
    try:
        return await user_service.get_user(user_id)
    except ResourceNotFoundException as e:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """Create a new user or update existing user based on email"""
    try:
        return await user_service.create_or_update_user(user_data)
    except Exception as e:
        logger.error(f"Error creating/updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create/update user")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update user profile"""
    # Check if user is updating their own profile or is an admin
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    try:
        return await user_service.update_user(user_id, user_data)
    except ResourceNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Delete user"""
    # Check if user is deleting their own account or is an admin
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    try:
        await user_service.delete_user(user_id)
    except ResourceNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


@router.put("/{user_id}/xp", response_model=UserResponse)
async def update_user_xp(
    user_id: str,
    xp_data: UpdateXPRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update user XP points"""
    try:
        return await user_service.add_xp(user_id, xp_data.xp_increase)
    except ResourceNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error updating user XP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user XP")


@router.put("/{user_id}/game-played", response_model=UserResponse)
async def increment_games_played(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Increment the games played counter for a user"""
    try:
        return await user_service.record_game_played(user_id)
    except ResourceNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error incrementing games played: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to increment games played")


@router.get("/", response_model=Dict[str, Any])
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    last_key: Optional[str] = None,
    user_service: UserService = Depends(get_user_service),
):
    """List users with pagination"""
    try:
        # Parse last_key if provided
        last_evaluated_key = None
        if last_key:
            try:
                import json
                last_evaluated_key = json.loads(last_key)
            except:
                raise HTTPException(status_code=400, detail="Invalid last_key format")
        
        return await user_service.list_users(limit, last_evaluated_key)
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get user by email"""
    try:
        user = await user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user by email")