from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from app.models.schemas.user import UserCreate, UserResponse, Token, GoogleTokenVerify
from app.services.user_services import UserService
from app.core.security import create_access_token, create_refresh_token
from datetime import timedelta
from app.core.config import get_settings
from app.api.dependencies import get_user_service
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/google-login", response_model=Token)
async def google_login(
    token_data: GoogleTokenVerify,
    user_service: UserService = Depends(get_user_service),
):
    """Login or register with Google OAuth using ID token verification"""
    try:
        from app.core.google_auth import verify_google_token
        
        # Verify the Google ID token and get user information
        google_user = verify_google_token(token_data.id_token)
        
        if not google_user.get("id") or not google_user.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google user data",
            )
        
        # Create or update user
        user_create = UserCreate(
            email=google_user.get("email"),
            name=google_user.get("name"),
            image=google_user.get("image")
        )
        
        user = await user_service.create_or_update_user(user_create)
        
        # Create tokens
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Google login",
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """Login with OAuth2 password flow (simplified for this example)"""
    # In a real implementation, this would validate credentials
    # Here we're just simulating it by finding a user with the provided username (email)
    user = await user_service.get_user_by_email(form_data.username)
    
    if not user:
        logger.warning(f"Login attempt failed: User not found for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real implementation, we would check the password here
    # For this example, we're skipping password validation
    
    # Create access and refresh tokens
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    user_service: UserService = Depends(get_user_service),
):
    """Get a new access token using a refresh token"""
    try:
        from app.core.security import decode_token
        from app.models.schemas.user import TokenPayload
        
        # Decode refresh token
        payload = decode_token(refresh_token)
        token_data = TokenPayload(**payload)
        
        # Check if token is a refresh token
        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user exists
        user = await user_service.get_user(token_data.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        # Create new refresh token
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        
        # Create new user
        new_user = await user_service.create_or_update_user(user_data)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )