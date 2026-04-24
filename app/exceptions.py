"""
Custom exceptions and exception handlers
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger


class RateLimitExceeded(Exception):
    """Raised when user exceeds rate limit"""
    def __init__(self, user_id: str, max_jobs: int):
        self.user_id = user_id
        self.max_jobs = max_jobs
        super().__init__(f"Rate limit exceeded for user {user_id}: max {max_jobs} active jobs")


class DocumentNotFound(Exception):
    """Raised when document is not found"""
    def __init__(self, document_id: str):
        self.document_id = document_id
        super().__init__(f"Document {document_id} not found")


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceptions"""
    logger.warning(f"Rate limit exceeded: {exc}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": str(exc),
            "user_id": exc.user_id,
            "max_active_jobs": exc.max_jobs
        }
    )


async def document_not_found_handler(request: Request, exc: DocumentNotFound):
    """Handle document not found exceptions"""
    logger.warning(f"Document not found: {exc.document_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "document_not_found",
            "message": str(exc),
            "document_id": exc.document_id
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )