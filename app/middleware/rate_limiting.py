from fastapi import Request, Response
import time
import logging
from typing import Dict, Tuple, Optional
from app.core.config import get_settings
from app.core.exceptions import RateLimitException

settings = get_settings()
logger = logging.getLogger(__name__)


class InMemoryStore:
    """Simple in-memory store for rate limiting"""
    
    def __init__(self):
        self.store: Dict[str, Tuple[int, float]] = {}
        self.cleanup_interval = 3600  # Clean up expired entries every hour
        self.last_cleanup = time.time()
    
    def get(self, key: str) -> Tuple[int, float]:
        """Get count and timestamp for a key"""
        self._cleanup()
        return self.store.get(key, (0, 0))
    
    def increment(self, key: str, expiry: float) -> Tuple[int, float]:
        """Increment counter for a key"""
        self._cleanup()
        count, _ = self.store.get(key, (0, 0))
        count += 1
        timestamp = time.time()
        self.store[key] = (count, timestamp + expiry)
        return count, timestamp
    
    def _cleanup(self):
        """Clean up expired entries"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self.store = {k: v for k, v in self.store.items() if v[1] > now}
            self.last_cleanup = now


class RedisStore:
    """Redis-based store for rate limiting (for production)"""
    
    def __init__(self, redis_url: str = None):
        # This would be implemented with a Redis client
        # For now, fallback to in-memory store
        self.store = InMemoryStore()
    
    def get(self, key: str) -> Tuple[int, float]:
        return self.store.get(key)
    
    def increment(self, key: str, expiry: float) -> Tuple[int, float]:
        return self.store.increment(key, expiry)


class RateLimitingMiddleware:
    """Middleware for rate limiting API requests"""
    
    def __init__(self, app):
        self.app = app
        # Use Redis in production, in-memory store for development
        self.store = RedisStore() if settings.DEBUG is False else InMemoryStore()
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.period = settings.RATE_LIMIT_PERIOD
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if not self.enabled:
            return await self.app(scope, receive, send)
            
        request = Request(scope, receive=receive)
        
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request.url.path):
            return await self.app(scope, receive, send)
        
        # Get client identifier (IP or authenticated user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        key = f"ratelimit:{client_id}:{request.url.path}"
        count, _ = self.store.get(key)
        
        if count >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            raise RateLimitException()
        
        # Increment counter
        count, _ = self.store.increment(key, self.period)
        
        # Store the original send
        original_send = send
        
        # Create a new send function to modify the response headers
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add rate limit headers to the response headers
                message.setdefault("headers", [])
                headers = message.get("headers", [])
                headers.append((b"X-RateLimit-Limit", str(self.max_requests).encode()))
                headers.append((b"X-RateLimit-Remaining", str(max(0, self.max_requests - count)).encode()))
                headers.append((b"X-RateLimit-Reset", str(int(time.time() + self.period)).encode()))
                message["headers"] = headers
            
            await original_send(message)
        
        # Process request with the modified send function
        return await self.app(scope, receive, send_with_headers)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use authenticated user ID if available
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Otherwise, use client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get first IP from X-Forwarded-For header
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path"""
        # Skip rate limiting for docs and health check
        skip_paths = [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
        ]
        
        return any(path.startswith(p) for p in skip_paths)