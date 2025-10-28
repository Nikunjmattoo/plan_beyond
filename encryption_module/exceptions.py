"""
Custom exceptions for encryption module.
Similar pattern to policy_checker for local error handling.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """Error codes for encryption module."""
    
    # Encryption/Decryption errors
    ENCRYPTION_FAILED = "ENCRYPTION_FAILED"
    DECRYPTION_FAILED = "DECRYPTION_FAILED"
    INVALID_KEY = "INVALID_KEY"
    INVALID_NONCE = "INVALID_NONCE"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    
    # Key management errors
    KEY_GENERATION_FAILED = "KEY_GENERATION_FAILED"
    KEY_NOT_FOUND = "KEY_NOT_FOUND"
    KEY_STORAGE_FAILED = "KEY_STORAGE_FAILED"
    KMS_ENCRYPTION_FAILED = "KMS_ENCRYPTION_FAILED"
    KMS_DECRYPTION_FAILED = "KMS_DECRYPTION_FAILED"
    
    # File operation errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_READ_FAILED = "FILE_READ_FAILED"
    FILE_WRITE_FAILED = "FILE_WRITE_FAILED"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    
    # Storage errors
    S3_UPLOAD_FAILED = "S3_UPLOAD_FAILED"
    S3_DOWNLOAD_FAILED = "S3_DOWNLOAD_FAILED"
    S3_DELETE_FAILED = "S3_DELETE_FAILED"
    S3_ACCESS_DENIED = "S3_ACCESS_DENIED"
    
    # Database errors
    DB_WRITE_FAILED = "DB_WRITE_FAILED"
    DB_READ_FAILED = "DB_READ_FAILED"
    DB_DELETE_FAILED = "DB_DELETE_FAILED"
    DUPLICATE_FILE_ID = "DUPLICATE_FILE_ID"
    
    # Access control errors
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    NOT_FILE_OWNER = "NOT_FILE_OWNER"
    ACCESS_NOT_FOUND = "ACCESS_NOT_FOUND"
    ACCESS_ALREADY_EXISTS = "ACCESS_ALREADY_EXISTS"
    ACCESS_REVOKED = "ACCESS_REVOKED"
    
    # Validation errors
    INVALID_JSON_FORMAT = "INVALID_JSON_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class BaseEncryptionException(Exception):
    """Base exception for all encryption module errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details
            }
        }


# ==================== ENCRYPTION/DECRYPTION EXCEPTIONS ====================

class EncryptionException(BaseEncryptionException):
    """Raised when encryption operation fails."""
    
    def __init__(self, message: str = "Encryption failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.ENCRYPTION_FAILED,
            status_code=500,
            details=details
        )


class DecryptionException(BaseEncryptionException):
    """Raised when decryption operation fails."""
    
    def __init__(self, message: str = "Decryption failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DECRYPTION_FAILED,
            status_code=500,
            details=details
        )


class InvalidKeyException(BaseEncryptionException):
    """Raised when encryption key is invalid."""
    
    def __init__(self, message: str = "Invalid encryption key", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_KEY,
            status_code=400,
            details=details
        )


class AuthenticationFailedException(BaseEncryptionException):
    """Raised when GCM authentication tag verification fails."""
    
    def __init__(self, message: str = "Data authentication failed - possible tampering detected", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            status_code=400,
            details=details
        )


# ==================== KEY MANAGEMENT EXCEPTIONS ====================

class KeyGenerationException(BaseEncryptionException):
    """Raised when key generation fails."""
    
    def __init__(self, message: str = "Failed to generate encryption key", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.KEY_GENERATION_FAILED,
            status_code=500,
            details=details
        )


class KeyNotFoundException(BaseEncryptionException):
    """Raised when encryption key is not found."""
    
    def __init__(self, message: str = "Encryption key not found", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.KEY_NOT_FOUND,
            status_code=404,
            details=details
        )


class KMSEncryptionException(BaseEncryptionException):
    """Raised when KMS encryption fails."""
    
    def __init__(self, message: str = "KMS key encryption failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.KMS_ENCRYPTION_FAILED,
            status_code=500,
            details=details
        )


class KMSDecryptionException(BaseEncryptionException):
    """Raised when KMS decryption fails."""
    
    def __init__(self, message: str = "KMS key decryption failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.KMS_DECRYPTION_FAILED,
            status_code=500,
            details=details
        )


# ==================== FILE OPERATION EXCEPTIONS ====================

class FileNotFoundException(BaseEncryptionException):
    """Raised when file is not found."""
    
    def __init__(self, message: str = "File not found", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.FILE_NOT_FOUND,
            status_code=404,
            details=details
        )


class FileTooLargeException(BaseEncryptionException):
    """Raised when file exceeds size limit."""
    
    def __init__(self, message: str = "File size exceeds limit", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.FILE_TOO_LARGE,
            status_code=413,
            details=details
        )


class InvalidFileTypeException(BaseEncryptionException):
    """Raised when file type is not allowed."""
    
    def __init__(self, message: str = "Invalid file type", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_FILE_TYPE,
            status_code=400,
            details=details
        )


# ==================== STORAGE EXCEPTIONS ====================

class S3UploadException(BaseEncryptionException):
    """Raised when S3 upload fails."""
    
    def __init__(self, message: str = "Failed to upload file to S3", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.S3_UPLOAD_FAILED,
            status_code=500,
            details=details
        )


class S3DownloadException(BaseEncryptionException):
    """Raised when S3 download fails."""
    
    def __init__(self, message: str = "Failed to download file from S3", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.S3_DOWNLOAD_FAILED,
            status_code=500,
            details=details
        )


class S3DeleteException(BaseEncryptionException):
    """Raised when S3 delete fails."""
    
    def __init__(self, message: str = "Failed to delete file from S3", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.S3_DELETE_FAILED,
            status_code=500,
            details=details
        )


class S3AccessDeniedException(BaseEncryptionException):
    """Raised when S3 access is denied."""
    
    def __init__(self, message: str = "S3 access denied", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.S3_ACCESS_DENIED,
            status_code=403,
            details=details
        )


# ==================== DATABASE EXCEPTIONS ====================

class DatabaseWriteException(BaseEncryptionException):
    """Raised when database write operation fails."""
    
    def __init__(self, message: str = "Failed to write to database", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_WRITE_FAILED,
            status_code=500,
            details=details
        )


class DatabaseReadException(BaseEncryptionException):
    """Raised when database read operation fails."""
    
    def __init__(self, message: str = "Failed to read from database", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_READ_FAILED,
            status_code=500,
            details=details
        )


class DuplicateFileException(BaseEncryptionException):
    """Raised when attempting to create duplicate file ID."""
    
    def __init__(self, message: str = "File ID already exists", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DUPLICATE_FILE_ID,
            status_code=409,
            details=details
        )


# ==================== ACCESS CONTROL EXCEPTIONS ====================

class UnauthorizedAccessException(BaseEncryptionException):
    """Raised when user attempts unauthorized file access."""
    
    def __init__(self, message: str = "Unauthorized access to file", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED_ACCESS,
            status_code=403,
            details=details
        )


class NotFileOwnerException(BaseEncryptionException):
    """Raised when non-owner attempts owner-only operation."""
    
    def __init__(self, message: str = "Only file owner can perform this operation", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FILE_OWNER,
            status_code=403,
            details=details
        )


class AccessNotFoundException(BaseEncryptionException):
    """Raised when file access record is not found."""
    
    def __init__(self, message: str = "File access not found", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.ACCESS_NOT_FOUND,
            status_code=404,
            details=details
        )


class AccessAlreadyExistsException(BaseEncryptionException):
    """Raised when attempting to create duplicate access."""
    
    def __init__(self, message: str = "Access already exists for this user", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.ACCESS_ALREADY_EXISTS,
            status_code=409,
            details=details
        )


# ==================== VALIDATION EXCEPTIONS ====================

class InvalidJSONException(BaseEncryptionException):
    """Raised when JSON parsing fails."""
    
    def __init__(self, message: str = "Invalid JSON format", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_JSON_FORMAT,
            status_code=400,
            details=details
        )


class ValidationException(BaseEncryptionException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_FAILED,
            status_code=400,
            details=details
        )