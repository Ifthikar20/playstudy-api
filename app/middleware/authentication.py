from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from typing import Optional, Dict, Any
import logging
import time
from app.core.config import get_settings
from app.core.security import decode_token
from app.models.schemas.user import TokenPayload
from app.services.user_services import UserService
from app.core.exceptions import AuthenticationException

settings = get_settings()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    user_service: UserService = Depends()
) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    if not token:
        raise AuthenticationException("Not authenticated")
    
    try:
        # Decode token
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        
        # Check if token is expired
        if token_data.exp < int(time.time()):
            raise AuthenticationException("Token expired")
            
        # Get user
        user = await user_service.get_user(token_data.sub)
        if user is None:
            raise AuthenticationException("User not found")
            
        return user
    except (JWTError, ValidationError) as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationException("Invalid authentication credentials")


class AuthenticationMiddleware:
    """Middleware for JWT authentication"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Create a new Starlette Request object
        request = Request(scope, receive=receive)
        
        # Define the call_next function
        async def call_next(request):
            # Create a new send function to capture the response
            response_started = False
            response_body = []
            
            async def send_wrapper(message):
                nonlocal response_started
                if message["type"] == "http.response.start":
                    response_started = True
                elif message["type"] == "http.response.body":
                    response_body.append(message.get("body", b""))
                await send(message)
                
            await self.app(scope, receive, send_wrapper)
            
        # Skip authentication for certain paths
        if self._should_skip_auth(request.url.path):
            return await self.app(scope, receive, send)
        
        # Extract token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await self.app(scope, receive, send)  # Let the route handler handle authentication
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            # Decode and validate token
            payload = decode_token(token)
            token_data = TokenPayload(**payload)
            
            # Check if token is expired
            if token_data.exp < int(time.time()):
                return await self.app(scope, receive, send)  # Let the route handler handle token expiry
                
            # Add user info to request state
            # We can't modify scope directly, so we need to recreate it
            scope["state"] = dict(scope.get("state", {}))
            scope["state"]["user_id"] = token_data.sub
            
        except (JWTError, ValidationError) as e:
            # Log the error but let the route handler decide on auth requirements
            logger.error(f"Token validation error: {str(e)}")
        
        return await self.app(scope, receive, send)
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path"""
        public_paths = [
            f"{settings.API_V1_STR}/auth/login",
            f"{settings.API_V1_STR}/auth/register",
            f"{settings.API_V1_STR}/docs",
            f"{settings.API_V1_STR}/openapi.json",
            "/docs",
            "/openapi.json",
            "/",
            "/health"
        ]
        
        return any(path.startswith(p) for p in public_paths)