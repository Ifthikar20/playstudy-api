from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from mangum import Mangum
from typing import Any
import uuid

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.exceptions import BaseAPIException, exception_handler
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.api.v1.router import api_router
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get app settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for PlayStudy.AI",
    version=settings.VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Exception handler
app.add_exception_handler(BaseAPIException, exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint for health checks"""
    return {"status": "online", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI endpoint with authentication"""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
        swagger_favicon_url="",
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Add security headers
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
    }
    
    for header_name, header_value in headers.items():
        response.headers[header_name] = header_value
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    # Get request ID from state if available
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "request_path": request.url.path,
            "request_method": request.method,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "SERVER_ERROR",
                "message": "An unexpected error occurred",
                "status": 500,
            }
        },
    )


# Create handler for AWS Lambda
handler = Mangum(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)