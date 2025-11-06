"""
Error handlers for encryption module.
Register these handlers with FastAPI router for consistent error responses.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from .exceptions import (
    BaseEncryptionException,
    EncryptionException,
    DecryptionException,
    KeyNotFoundException,
    FileNotFoundException,
    UnauthorizedAccessException,
    ValidationException
)


logger = logging.getLogger(__name__)


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        error_code: Error code enum value
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        JSONResponse with error details
    """
    response_body = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        response_body["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=response_body
    )


async def base_encryption_exception_handler(
    request: Request,
    exc: BaseEncryptionException
) -> JSONResponse:
    """
    Handler for all BaseEncryptionException and its subclasses.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
    
    Returns:
        JSONResponse with error details
    """
    # Log the error
    logger.error(
        f"Encryption error occurred: {exc.error_code.value}",
        extra={
            "error_code": exc.error_code.value,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return formatted error response
    return create_error_response(
        error_code=exc.error_code.value,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handler for unexpected exceptions that aren't caught by specific handlers.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
    
    Returns:
        JSONResponse with generic error message
    """
    # Log the unexpected error with full traceback
    logger.exception(
        "Unexpected error in encryption module",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    # Return generic error (don't expose internal details)
    return create_error_response(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        details={"exception_type": type(exc).__name__}
    )


# Exception handler mapping for easy registration
EXCEPTION_HANDLERS = {
    BaseEncryptionException: base_encryption_exception_handler,
    Exception: generic_exception_handler
}


def register_error_handlers(app):
    """
    Register all error handlers with the main FastAPI app (not router).
    
    Usage in main.py:
        from app.encryption_module.error_handlers import register_error_handlers
        register_error_handlers(app)
    
    Args:
        app: FastAPI application instance
    """
    for exception_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_class, handler)


def log_error_context(
    error_type: str,
    message: str,
    **kwargs
):
    """
    Centralized error logging with context.
    
    Args:
        error_type: Type of error (e.g., 'encryption', 'key_management')
        message: Error message
        **kwargs: Additional context to log
    """
    logger.error(
        f"[{error_type.upper()}] {message}",
        extra={
            "error_type": error_type,
            **kwargs
        }
    )