"""
Error codes and exception handling for Reminder System
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


# ==========================================
# ERROR CODES
# ==========================================

class ReminderErrorCode:
    """Error codes for reminder operations"""
    
    # Reminder errors (4000-4099)
    REMINDER_NOT_FOUND = "REM_4000"
    REMINDER_ALREADY_EXISTS = "REM_4001"
    REMINDER_ACCESS_DENIED = "REM_4002"
    REMINDER_INVALID_STATUS = "REM_4003"
    REMINDER_INVALID_CATEGORY = "REM_4004"
    REMINDER_INVALID_URGENCY = "REM_4005"
    REMINDER_INVALID_DATE = "REM_4006"
    REMINDER_CREATION_FAILED = "REM_4007"
    REMINDER_UPDATE_FAILED = "REM_4008"
    REMINDER_DELETE_FAILED = "REM_4009"
    
    # Preference errors (4100-4199)
    PREFERENCE_NOT_FOUND = "REM_4100"
    PREFERENCE_CREATION_FAILED = "REM_4101"
    PREFERENCE_UPDATE_FAILED = "REM_4102"
    PREFERENCE_INVALID_TIMEZONE = "REM_4103"
    PREFERENCE_INVALID_TIME = "REM_4104"
    
    # Validation errors (4200-4299)
    VALIDATION_FAILED = "REM_4200"
    INVALID_USER_ID = "REM_4201"
    INVALID_VAULT_FILE_ID = "REM_4202"
    INVALID_REMINDER_ID = "REM_4203"
    INVALID_DATE_RANGE = "REM_4204"
    INVALID_SNOOZE_DURATION = "REM_4205"
    
    # Database errors (4300-4399)
    DATABASE_ERROR = "REM_4300"
    DATABASE_CONNECTION_FAILED = "REM_4301"
    DATABASE_QUERY_FAILED = "REM_4302"
    DATABASE_COMMIT_FAILED = "REM_4303"
    
    # Email errors (4400-4499)
    EMAIL_SEND_FAILED = "REM_4400"
    EMAIL_CONNECTION_FAILED = "REM_4401"
    EMAIL_INVALID_ADDRESS = "REM_4402"
    
    # Scheduler errors (4500-4599)
    SCHEDULER_FAILED = "REM_4500"
    SENDER_FAILED = "REM_4501"
    ESCALATOR_FAILED = "REM_4502"


# ==========================================
# CUSTOM EXCEPTIONS
# ==========================================

class ReminderException(HTTPException):
    """Base exception for reminder system"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "details": self.details
            }
        )


class ReminderNotFoundException(ReminderException):
    """Reminder not found"""
    
    def __init__(self, reminder_id: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ReminderErrorCode.REMINDER_NOT_FOUND,
            message=f"Reminder '{reminder_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"reminder_id": reminder_id}
        )


class ReminderAccessDeniedException(ReminderException):
    """User doesn't have access to reminder"""
    
    def __init__(self, reminder_id: str, user_id: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ReminderErrorCode.REMINDER_ACCESS_DENIED,
            message=f"User '{user_id}' does not have access to reminder '{reminder_id}'",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {"reminder_id": reminder_id, "user_id": user_id}
        )


class ReminderAlreadyExistsException(ReminderException):
    """Duplicate reminder"""
    
    def __init__(self, details: Optional[Dict] = None):
        super().__init__(
            error_code=ReminderErrorCode.REMINDER_ALREADY_EXISTS,
            message="A reminder for this file and date already exists",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ReminderValidationException(ReminderException):
    """Validation failed"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ReminderErrorCode.VALIDATION_FAILED,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class PreferenceNotFoundException(ReminderException):
    """Preference not found"""
    
    def __init__(self, user_id: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ReminderErrorCode.PREFERENCE_NOT_FOUND,
            message=f"Reminder preferences not found for user '{user_id}'",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"user_id": user_id}
        )


class ReminderDatabaseException(ReminderException):
    """Database operation failed"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=ReminderErrorCode.DATABASE_ERROR,
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


# ==========================================
# ERROR RESPONSE SCHEMAS
# ==========================================

ERROR_RESPONSES = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "REM_4200",
                    "message": "Validation failed",
                    "details": {"field": "reminder_date", "error": "Date must be in the future"}
                }
            }
        }
    },
    403: {
        "description": "Forbidden - Access Denied",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "REM_4002",
                    "message": "User does not have access to this reminder",
                    "details": {"reminder_id": "abc123", "user_id": "user123"}
                }
            }
        }
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "REM_4000",
                    "message": "Reminder not found",
                    "details": {"reminder_id": "abc123"}
                }
            }
        }
    },
    409: {
        "description": "Conflict - Duplicate",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "REM_4001",
                    "message": "A reminder for this file and date already exists",
                    "details": {"vault_file_id": "file123", "reminder_date": "2025-12-31"}
                }
            }
        }
    },
    422: {
        "description": "Unprocessable Entity - Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "REM_4200",
                    "message": "Validation failed",
                    "details": {"errors": ["Invalid date format", "Missing required field"]}
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "REM_4300",
                    "message": "Database error occurred",
                    "details": {"error": "Connection timeout"}
                }
            }
        }
    }
}