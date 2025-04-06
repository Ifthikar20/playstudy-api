from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Union, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAPIException(HTTPException):
    """Base API exception with error code and message"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        detail: Union[str, Dict[str, Any]],
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class ResourceNotFoundException(BaseAPIException):
    """Exception for resource not found errors"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            detail=f"{resource_type} with id {resource_id} not found",
        )

class AuthenticationException(BaseAPIException):
    """Exception for authentication errors"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class AuthorizationException(BaseAPIException):
    """Exception for authorization errors"""
    def __init__(self, detail: str = "Not authorized to access this resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_FAILED",
            detail=detail,
        )

class ValidationException(BaseAPIException):
    """Exception for validation errors"""
    def __init__(self, detail: Union[str, Dict[str, Any]]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            detail=detail,
        )

class RateLimitException(BaseAPIException):
    """Exception for rate limit exceeded"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            detail=detail,
        )

class ServerException(BaseAPIException):
    """Exception for server errors"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SERVER_ERROR",
            detail=detail,
        )

async def exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Global exception handler for API exceptions"""
    # Log the exception
    logger.error(
        f"Exception occurred: {exc.error_code} - {exc.detail}",
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
        },
    )
    
    # Return formatted error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "status": exc.status_code,
            }
        },
        headers=exc.headers,
    )

# Additional exception handlers can be added for specific error types