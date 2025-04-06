"""Development dependencies for easier local development"""

from fastapi import Request
from typing import Dict, Any
import uuid
from datetime import datetime
from app.models.schemas.user import UserResponse

async def get_test_user() -> Dict[str, Any]:
    """Development dependency that returns a mock user without authentication"""
    # Return a mocked user for development
    return UserResponse(
        id=str(uuid.uuid4()),
        email="dev@example.com",
        name="Dev User",
        image=None,
        created_at=datetime.utcnow(),
        updated_at=None,
        last_login=datetime.utcnow(),
        xp_points=1000,
        level=11,
        games_played=5
    ).model_dump()