from typing import Any, Dict, List, Optional
from app.repositories.base import BaseRepository
from app.models.domain.user import User
from app.core.config import get_settings
import logging
from datetime import datetime

settings = get_settings()
logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user data"""
    
    def __init__(self):
        """Initialize user repository"""
        super().__init__(settings.USERS_TABLE, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            # Query by email index
            result = await self.query_by_index(
                index_name="email-index",
                key_condition_expression="email = :email",
                expression_attribute_values={":email": email},
                limit=1
            )
            
            if result["count"] == 0:
                return None
                
            return result["items"][0]
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def create_or_update_user(self, email: str, name: Optional[str] = None, image: Optional[str] = None) -> User:
        """Create a new user or update existing user by email"""
        # Check if user exists
        existing_user = await self.get_by_email(email)
        
        if existing_user:
            # Update user
            updates = {
                "updated_at": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat()
            }
            
            if name:
                updates["name"] = name
                
            if image:
                updates["image"] = image
                
            return await self.update(existing_user.id, updates)
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                image=image,
                created_at=datetime.utcnow(),
                updated_at=None,
                last_login=datetime.utcnow(),
                xp_points=0,
                level=1,
                games_played=0
            )
            
            return await self.create(user)
    
    async def update_profile(self, user_id: str, name: Optional[str] = None, image: Optional[str] = None) -> User:
        """Update user profile"""
        updates = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if name:
            updates["name"] = name
            
        if image:
            updates["image"] = image
            
        return await self.update(user_id, updates)
    
    async def update_xp(self, user_id: str, xp_increase: int) -> User:
        """Add XP to user and update level"""
        # Get current user
        user = await self.get(user_id)
        
        # Calculate new XP and level
        new_xp = user.xp_points + xp_increase
        # Simple level calculation: 100 XP per level, max level 100
        new_level = min(max(1, int(new_xp / 100) + 1), 100)
        
        # Update user
        updates = {
            "xp_points": new_xp,
            "level": new_level,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return await self.update(user_id, updates)
    
    async def increment_games_played(self, user_id: str) -> User:
        """Increment games played counter"""
        # Get current user
        user = await self.get(user_id)
        
        # Update user
        updates = {
            "games_played": user.games_played + 1,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return await self.update(user_id, updates)