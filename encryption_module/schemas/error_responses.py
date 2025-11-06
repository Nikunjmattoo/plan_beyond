"""
Error response schemas for OpenAPI documentation.
Use these in router responses to document possible error responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(False, description="Always false for error responses")
    error: ErrorDetail = Field(..., description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "ENCRYPTION_FAILED",
                    "message": "Failed to encrypt file data",
                    "details": {
                        "file_id": "abc123",
                        "reason": "Invalid encryption key format"
                    }
                }
            }
        }


# Specific error response examples for documentation
class EncryptionErrorResponse(ErrorResponse):
    """Error response for encryption failures."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "ENCRYPTION_FAILED",
                    "message": "Failed to encrypt file data",
                    "details": {"file_id": "abc123"}
                }
            }
        }


class DecryptionErrorResponse(ErrorResponse):
    """Error response for decryption failures."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "DECRYPTION_FAILED",
                    "message": "Failed to decrypt file data",
                    "details": {"file_id": "abc123"}
                }
            }
        }


class UnauthorizedErrorResponse(ErrorResponse):
    """Error response for unauthorized access."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED_ACCESS",
                    "message": "You do not have access to this file",
                    "details": {"file_id": "abc123"}
                }
            }
        }


class NotFoundErrorResponse(ErrorResponse):
    """Error response for resource not found."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "FILE_NOT_FOUND",
                    "message": "File not found",
                    "details": {"file_id": "abc123"}
                }
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation failures."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "Input validation failed",
                    "details": {
                        "field": "file_size",
                        "reason": "File size exceeds 10MB limit"
                    }
                }
            }
        }


class S3ErrorResponse(ErrorResponse):
    """Error response for S3 operation failures."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "S3_UPLOAD_FAILED",
                    "message": "Failed to upload file to S3",
                    "details": {
                        "bucket": "theplanbeyond",
                        "key": "vault/abc123.enc"
                    }
                }
            }
        }


class KMSErrorResponse(ErrorResponse):
    """Error response for KMS operation failures."""
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "KMS_ENCRYPTION_FAILED",
                    "message": "Failed to encrypt key with KMS",
                    "details": {"key_id": "vault-master-key"}
                }
            }
        }


# Response model mapping for router documentation
ERROR_RESPONSES = {
    400: {"model": ValidationErrorResponse, "description": "Bad request - validation failed"},
    403: {"model": UnauthorizedErrorResponse, "description": "Forbidden - unauthorized access"},
    404: {"model": NotFoundErrorResponse, "description": "Not found - resource doesn't exist"},
    409: {"model": ErrorResponse, "description": "Conflict - resource already exists"},
    413: {"model": ValidationErrorResponse, "description": "Payload too large - file exceeds size limit"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}