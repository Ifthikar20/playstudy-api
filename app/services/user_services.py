from app.repositories.user_repository import UserRepository
from app.models.domain.user import User
from app.models.schemas.user import UserCreate, UserUpdate, UserResponse
from typing import Optional, List, Dict, Any
import logging
from app.core.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations"""
    
    def __init__(self, user_repository: UserRepository = None):
        self.user_repository = user_repository or UserRepository()
    
    async def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID"""
        user = await self.user_repository.get(user_id)
        return UserResponse.model_validate(user.to_dict())
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None
        return UserResponse.model_validate(user.to_dict())
    
    async def create_or_update_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user or update if exists"""
        user = await self.user_repository.create_or_update_user(
            email=user_data.email,
            name=user_data.name,
            image=user_data.image
        )
        return UserResponse.model_validate(user.to_dict())
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserResponse:
        """Update user profile"""
        user = await self.user_repository.update_profile(
            user_id=user_id,
            name=user_data.name,
            image=user_data.image
        )
        return UserResponse.model_validate(user.to_dict())
    
    async def delete_user(self, user_id: str) -> None:
        """Delete user"""
        await self.user_repository.delete(user_id)
    
    async def add_xp(self, user_id: str, xp_increase: int) -> UserResponse:
        """Add XP to user and update level"""
        user = await self.user_repository.update_xp(user_id, xp_increase)
        return UserResponse.model_validate(user.to_dict())
    
    async def record_game_played(self, user_id: str) -> UserResponse:
        """Record that user played a game"""
        user = await self.user_repository.increment_games_played(user_id)
        return UserResponse.model_validate(user.to_dict())
    
    async def list_users(self, limit: int = 100, last_key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List users with pagination"""
        result = await self.user_repository.list(limit, last_key)
        return {
            "items": [UserResponse.model_validate(user.to_dict()) for user in result["items"]],
            "count": result["count"],
            "last_evaluated_key": result["last_evaluated_key"]
        }
    
    async def calculate_level(self, xp: int) -> int:
        """Calculate user level based on XP"""
        # Simple level calculation: 100 XP per level, max level 100
        return min(max(1, int(xp / 100) + 1), 100)