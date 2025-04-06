from fastapi import Depends, Request
from app.services.user_services import UserService
from app.repositories.user_repository import UserRepository
from typing import Generator, Dict, Any


def get_user_repository() -> UserRepository:
    """Dependency for UserRepository"""
    return UserRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Dependency for UserService"""
    return UserService(user_repository=user_repo)


def get_request_id(request: Request) -> str:
    """Get the request ID from request state"""
    return getattr(request.state, "request_id", "unknown")


def get_user_id_from_request(request: Request) -> str:
    """Get user ID from request state (set by auth middleware)"""
    return getattr(request.state, "user_id", None)