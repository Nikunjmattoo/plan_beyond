"""Error response schemas for API documentation."""

from .error_responses import (
    ErrorDetail,
    ErrorResponse,
    EncryptionErrorResponse,
    DecryptionErrorResponse,
    UnauthorizedErrorResponse,
    NotFoundErrorResponse,
    ValidationErrorResponse,
    S3ErrorResponse,
    KMSErrorResponse,
    ERROR_RESPONSES
)

__all__ = [
    'ErrorDetail',
    'ErrorResponse',
    'EncryptionErrorResponse',
    'DecryptionErrorResponse',
    'UnauthorizedErrorResponse',
    'NotFoundErrorResponse',
    'ValidationErrorResponse',
    'S3ErrorResponse',
    'KMSErrorResponse',
    'ERROR_RESPONSES',
]