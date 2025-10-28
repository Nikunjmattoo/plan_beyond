"""
Rate limiting for encryption module operations.
Uses slowapi for per-user rate limiting.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Callable
import logging

logger = logging.getLogger(__name__)


# Custom key function to rate limit by user ID (from JWT token)
def get_user_id_from_request(request: Request) -> str:
    """
    Extract user ID from request for rate limiting.
    Falls back to IP address if user ID not available.
    """
    # Try to get user ID from request state (set by get_current_user_id dependency)
    if hasattr(request.state, 'user_id'):
        return f"user:{request.state.user_id}"
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


# Initialize rate limiter
limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=["1000/day"],  # Global default: 1000 requests per day
    storage_uri="memory://",  # Use in-memory storage (change to Redis for production)
)


# Custom rate limit exceeded handler
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    Returns a proper JSON response with retry information.
    """
    logger.warning(
        f"Rate limit exceeded for {get_user_id_from_request(request)} "
        f"on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after": "Please wait before making more requests",
                    "limit": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"
                }
            }
        }
    )


def register_rate_limiter(app):
    """
    Register rate limiter with FastAPI app.
    
    Usage in main.py:
        from app.encryption_module.rate_limiter import register_rate_limiter
        register_rate_limiter(app)
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    logger.info("Rate limiter registered successfully")