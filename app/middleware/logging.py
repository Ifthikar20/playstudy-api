from fastapi import Request, Response
import logging
import time
import uuid
from datetime import datetime
from typing import Callable, Awaitable
import json

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Middleware for logging all HTTP requests and responses"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Create the request object
        request = Request(scope)
        
        # Add request ID to scope state
        scope["state"] = dict(scope.get("state", {}))
        scope["state"]["request_id"] = request_id
        
        # Set up request information
        path = request.url.path
        method = request.method
        
        # Skip logging for certain paths
        if self._should_skip_logging(path):
            return await self.app(scope, receive, send)
            
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Get client information
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Get authenticated user ID if available
        user_id = scope.get("state", {}).get("user_id", None)
        
        # Log start of request
        start_time = time.time()
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_host,
                "user_agent": user_agent,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        # Store the original send function
        original_send = send
        
        # Create a send function to capture response info and add headers
        status_code = None
        
        async def send_with_logging(message):
            nonlocal status_code
            
            if message["type"] == "http.response.start":
                # Capture status code
                status_code = message["status"]
                
                # Add request ID header
                message.setdefault("headers", [])
                headers = message.get("headers", [])
                headers.append((b"X-Request-ID", request_id.encode()))
                message["headers"] = headers
                
            await original_send(message)
        
        try:
            # Process the request
            await self.app(scope, receive, send_with_logging)
            
            # Calculate request duration
            duration_ms = round((time.time() - start_time) * 1000)
            
            # Log completion of request
            if status_code is not None:
                logger.info(
                    f"Request completed: {method} {path} {status_code} in {duration_ms}ms",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "user_id": user_id,
                    },
                )
            
        except Exception as e:
            # Calculate request duration
            duration_ms = round((time.time() - start_time) * 1000)
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} in {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "user_id": user_id,
                },
                exc_info=True,
            )
            
            # Re-raise the exception
            raise
    
    def _should_skip_logging(self, path: str) -> bool:
        """Check if logging should be skipped for this path"""
        # Skip logging for health checks and static files
        skip_paths = [
            "/health",
            "/static",
        ]
        
        return any(path.startswith(p) for p in skip_paths)


class RequestBodyLoggingMiddleware:
    """Additional middleware for logging request and response bodies"""
    
    def __init__(
        self,
        app,
        max_body_size: int = 10000,  # Log up to 10KB of body
        sensitive_paths: list = None,  # Paths to skip body logging
    ):
        self.app = app
        self.max_body_size = max_body_size
        self.sensitive_paths = sensitive_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Create a request object
        request = Request(scope)
        
        # Skip body logging for sensitive paths
        if any(request.url.path.startswith(path) for path in self.sensitive_paths):
            return await self.app(scope, receive, send)
        
        # Get request ID
        request_id = scope.get("state", {}).get("request_id", str(uuid.uuid4()))
        
        # Log request body for appropriate content types
        content_type = request.headers.get("Content-Type", "")
        if "application/json" in content_type:
            # We need to capture the request body, so we wrap the receive function
            # to save the body contents when it's read
            body_chunks = []
            
            async def receive_with_logging():
                message = await receive()
                
                if message["type"] == "http.request":
                    body_chunks.append(message.get("body", b""))
                    
                    # If this is the last piece of the body, log it
                    if not message.get("more_body", False) and body_chunks:
                        body = b"".join(body_chunks)
                        try:
                            body_str = body.decode()
                            
                            # Truncate if necessary
                            if len(body_str) > self.max_body_size:
                                body_str = body_str[:self.max_body_size] + "... [truncated]"
                            
                            # Try to pretty print JSON
                            try:
                                json_body = json.loads(body_str)
                                # Sanitize sensitive fields
                                json_body = self._sanitize_json(json_body)
                                body_str = json.dumps(json_body, indent=2)
                            except json.JSONDecodeError:
                                # Not JSON, leave as is
                                pass
                                
                            # Log request body
                            logger.debug(
                                f"Request body: {request.method} {request.url.path}",
                                extra={
                                    "request_id": request_id,
                                    "request_body": body_str,
                                },
                            )
                        except Exception as e:
                            logger.warning(f"Error processing request body: {str(e)}")
                        
                return message
                
            # Process the request with our custom receive function
            return await self.app(scope, receive_with_logging, send)
        
        # No need to log the body, just process the request
        return await self.app(scope, receive, send)
    
    def _sanitize_json(self, data):
        """Sanitize sensitive fields in JSON data"""
        if not isinstance(data, dict):
            return data
            
        # Define sensitive fields to mask
        sensitive_fields = [
            "password", "password_confirm", "current_password", 
            "new_password", "token", "access_token", "refresh_token",
            "api_key", "secret", "credit_card", "card_number",
            "cvv", "cvc", "ssn", "social_security"
        ]
        
        # Create a sanitized copy
        result = {}
        
        for key, value in data.items():
            # Mask sensitive fields
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                result[key] = "********"
            # Recursively sanitize nested objects
            elif isinstance(value, dict):
                result[key] = self._sanitize_json(value)
            # Recursively sanitize lists
            elif isinstance(value, list):
                result[key] = [
                    self._sanitize_json(item) if isinstance(item, dict) else item 
                    for item in value
                ]
            # Keep other values as is
            else:
                result[key] = value
                
        return result
    
    async def _get_request_body(self, request: Request) -> str:
        """Get request body as string"""
        try:
            body = await request.body()
            body_str = body.decode()
            
            # Try to pretty print JSON
            try:
                json_body = json.loads(body_str)
                # Sanitize sensitive fields
                json_body = self._sanitize_json(json_body)
                body_str = json.dumps(json_body, indent=2)
            except json.JSONDecodeError:
                # Not JSON, leave as is
                pass
                
            return body_str
        except Exception as e:
            logger.warning(f"Error getting request body: {str(e)}")
            return ""
    
    def _sanitize_json(self, data):
        """Sanitize sensitive fields in JSON data"""
        if not isinstance(data, dict):
            return data
            
        # Define sensitive fields to mask
        sensitive_fields = [
            "password", "password_confirm", "current_password", 
            "new_password", "token", "access_token", "refresh_token",
            "api_key", "secret", "credit_card", "card_number",
            "cvv", "cvc", "ssn", "social_security"
        ]
        
        # Create a sanitized copy
        result = {}
        
        for key, value in data.items():
            # Mask sensitive fields
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                result[key] = "********"
            # Recursively sanitize nested objects
            elif isinstance(value, dict):
                result[key] = self._sanitize_json(value)
            # Recursively sanitize lists
            elif isinstance(value, list):
                result[key] = [
                    self._sanitize_json(item) if isinstance(item, dict) else item 
                    for item in value
                ]
            # Keep other values as is
            else:
                result[key] = value
                
        return result