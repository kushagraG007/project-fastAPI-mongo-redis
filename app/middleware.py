"""
Custom middleware for request/response logging
"""

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    
    Adds:
    - Request ID to each request
    - Request/response timing
    - Request details logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state (accessible in routes)
        request.state.request_id = request_id
        
        # Log incoming request
        logger.info(
            f"→ Request {request_id[:8]} | {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request and time it
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"← Response {request_id[:8]} | Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"✗ Error {request_id[:8]} | {str(e)} | Time: {process_time:.3f}s",
                exc_info=True
            )
            raise