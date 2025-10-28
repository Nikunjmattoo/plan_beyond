"""
Input validation for encryption module.
Enforces file size limits, MIME type restrictions, and form data validation.
"""

import json
from typing import Dict, Any, Optional
from fastapi import UploadFile
import logging

from .core.config import (
    MAX_SOURCE_FILE_SIZE,
    MAX_SOURCE_FILE_SIZE_MB,
    MAX_FORM_DATA_SIZE,
    MAX_FORM_DATA_SIZE_MB,
    ALLOWED_MIME_TYPES,
    ALLOWED_FILE_TYPES_DISPLAY,
    MAX_FIELD_COUNT,
    MAX_FIELD_LENGTH,
    MAX_FIELD_NAME_LENGTH
)
from .exceptions import (
    FileTooLargeException,
    InvalidFileTypeException,
    ValidationException,
    InvalidJSONException
)

logger = logging.getLogger(__name__)


def validate_file_size(file_size: int, filename: str):
    """
    Validate file size is within limits.
    
    Args:
        file_size: Size of file in bytes
        filename: Name of file (for error message)
        
    Raises:
        FileTooLargeException: If file exceeds size limit
    """
    if file_size > MAX_SOURCE_FILE_SIZE:
        logger.warning(
            f"File size validation failed: {filename} ({file_size} bytes) "
            f"exceeds limit ({MAX_SOURCE_FILE_SIZE} bytes)"
        )
        raise FileTooLargeException(
            f"File '{filename}' is too large. Maximum allowed size is {MAX_SOURCE_FILE_SIZE_MB:.1f} MB",
            details={
                "filename": filename,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "max_size_bytes": MAX_SOURCE_FILE_SIZE,
                "max_size_mb": MAX_SOURCE_FILE_SIZE_MB
            }
        )
    
    logger.debug(f"File size validation passed: {filename} ({file_size} bytes)")


def validate_mime_type(mime_type: str, filename: str):
    """
    Validate MIME type is allowed.
    
    Args:
        mime_type: MIME type of file
        filename: Name of file (for error message)
        
    Raises:
        InvalidFileTypeException: If MIME type not allowed
    """
    if mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(
            f"MIME type validation failed: {filename} has type '{mime_type}' "
            f"which is not in allowed list"
        )
        raise InvalidFileTypeException(
            f"File type '{mime_type}' is not allowed. Allowed types: {ALLOWED_FILE_TYPES_DISPLAY}",
            details={
                "filename": filename,
                "provided_mime_type": mime_type,
                "allowed_mime_types": ALLOWED_MIME_TYPES
            }
        )
    
    logger.debug(f"MIME type validation passed: {filename} ({mime_type})")


async def validate_upload_file(file: UploadFile) -> bytes:
    """
    Validate and read uploaded file.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        bytes: File content
        
    Raises:
        FileTooLargeException: If file too large
        InvalidFileTypeException: If MIME type not allowed
        ValidationException: If file cannot be read
    """
    if not file:
        raise ValidationException(
            "No file provided",
            details={"error": "file is required"}
        )
    
    # Validate MIME type first (before reading entire file)
    validate_mime_type(file.content_type, file.filename)
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        logger.exception(f"Failed to read uploaded file: {file.filename}")
        raise ValidationException(
            f"Failed to read uploaded file: {str(e)}",
            details={
                "filename": file.filename,
                "error": str(e)
            }
        )
    
    # Validate file size
    validate_file_size(len(file_content), file.filename)
    
    logger.info(
        f"Upload file validation passed: {file.filename} "
        f"({len(file_content)} bytes, {file.content_type})"
    )
    
    return file_content


def validate_form_data(form_data_str: str) -> Dict[str, Any]:
    """
    Validate and parse form data JSON string.
    
    Args:
        form_data_str: JSON string of form data
        
    Returns:
        Dict: Parsed form data
        
    Raises:
        InvalidJSONException: If JSON is invalid
        ValidationException: If form data exceeds limits
    """
    # Check size before parsing
    form_data_size = len(form_data_str.encode('utf-8'))
    if form_data_size > MAX_FORM_DATA_SIZE:
        logger.warning(
            f"Form data size validation failed: {form_data_size} bytes "
            f"exceeds limit ({MAX_FORM_DATA_SIZE} bytes)"
        )
        raise ValidationException(
            f"Form data is too large. Maximum allowed size is {MAX_FORM_DATA_SIZE_MB:.1f} MB",
            details={
                "form_data_size_bytes": form_data_size,
                "form_data_size_mb": round(form_data_size / (1024 * 1024), 2),
                "max_size_bytes": MAX_FORM_DATA_SIZE,
                "max_size_mb": MAX_FORM_DATA_SIZE_MB
            }
        )
    
    # Parse JSON
    try:
        form_data = json.loads(form_data_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Form data JSON parsing failed: {str(e)}")
        raise InvalidJSONException(
            "Invalid form data JSON format",
            details={
                "error": str(e),
                "position": e.pos if hasattr(e, 'pos') else None
            }
        )
    
    # Validate it's a dictionary
    if not isinstance(form_data, dict):
        raise ValidationException(
            "Form data must be a JSON object (dictionary)",
            details={
                "provided_type": type(form_data).__name__,
                "expected_type": "dict"
            }
        )
    
    # Validate field count
    field_count = len(form_data)
    if field_count > MAX_FIELD_COUNT:
        logger.warning(
            f"Form data field count validation failed: {field_count} fields "
            f"exceeds limit ({MAX_FIELD_COUNT})"
        )
        raise ValidationException(
            f"Too many fields in form data. Maximum allowed is {MAX_FIELD_COUNT} fields",
            details={
                "field_count": field_count,
                "max_field_count": MAX_FIELD_COUNT
            }
        )
    
    # Validate each field
    for field_name, field_value in form_data.items():
        # Validate field name length
        if len(field_name) > MAX_FIELD_NAME_LENGTH:
            raise ValidationException(
                f"Field name '{field_name[:50]}...' is too long",
                details={
                    "field_name": field_name[:100],
                    "field_name_length": len(field_name),
                    "max_field_name_length": MAX_FIELD_NAME_LENGTH
                }
            )
        
        # Convert field value to string for length check
        field_value_str = str(field_value) if not isinstance(field_value, str) else field_value
        
        # Validate field value length
        if len(field_value_str) > MAX_FIELD_LENGTH:
            logger.warning(
                f"Field '{field_name}' length validation failed: {len(field_value_str)} "
                f"characters exceeds limit ({MAX_FIELD_LENGTH})"
            )
            raise ValidationException(
                f"Field '{field_name}' value is too long. Maximum allowed is {MAX_FIELD_LENGTH} characters",
                details={
                    "field_name": field_name,
                    "field_value_length": len(field_value_str),
                    "max_field_length": MAX_FIELD_LENGTH
                }
            )
    
    logger.info(
        f"Form data validation passed: {field_count} fields, "
        f"{form_data_size} bytes"
    )
    
    return form_data


def validate_creation_mode(creation_mode: str):
    """
    Validate creation mode is valid.
    
    Args:
        creation_mode: Creation mode string
        
    Raises:
        ValidationException: If creation mode is invalid
    """
    valid_modes = ['import', 'manual']
    
    if creation_mode not in valid_modes:
        raise ValidationException(
            f"Invalid creation mode: '{creation_mode}'",
            details={
                "provided_mode": creation_mode,
                "valid_modes": valid_modes
            }
        )
    
    logger.debug(f"Creation mode validation passed: {creation_mode}")


def validate_template_id(template_id: str):
    """
    Validate template ID is not empty.
    
    Args:
        template_id: Template identifier
        
    Raises:
        ValidationException: If template ID is invalid
    """
    if not template_id or not template_id.strip():
        raise ValidationException(
            "Template ID cannot be empty",
            details={"template_id": template_id}
        )
    
    if len(template_id) > 100:
        raise ValidationException(
            "Template ID is too long",
            details={
                "template_id_length": len(template_id),
                "max_length": 100
            }
        )
    
    logger.debug(f"Template ID validation passed: {template_id}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    import re
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename