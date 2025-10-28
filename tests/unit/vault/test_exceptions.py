"""
Module 3: Vault - Exception Tests (Tests 114-125)

Tests custom exception classes for encryption module.
"""
import pytest

from encryption_module.exceptions import (
    EncryptionException,
    DecryptionException,
    KeyGenerationException,
    KMSDecryptionException,
    S3UploadException,
    S3DownloadException,
    FileTooLargeException,
    InvalidFileTypeException,
    InvalidJSONException,
    UnauthorizedAccessException,
    FileNotFoundException,
    ValidationException,
    ErrorCode
)


# ==============================================
# ENCRYPTION/DECRYPTION EXCEPTION TESTS (Tests 114-117)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encryption_exception_raised():
    """
    Test #114: EncryptionException includes correct error code and status
    """
    # Arrange
    message = "Test encryption failure"
    details = {"reason": "invalid_data"}

    # Act
    exception = EncryptionException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.ENCRYPTION_FAILED
    assert exception.status_code == 500
    assert exception.details == details


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decryption_exception_raised():
    """
    Test #115: DecryptionException includes correct error code and status
    """
    # Arrange
    message = "Test decryption failure"
    details = {"reason": "invalid_key"}

    # Act
    exception = DecryptionException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.DECRYPTION_FAILED
    assert exception.status_code == 500
    assert exception.details == details


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_key_generation_exception_raised():
    """
    Test #116: KeyGenerationException includes correct error code and status
    """
    # Arrange
    message = "Failed to generate key"

    # Act
    exception = KeyGenerationException(message=message)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.KEY_GENERATION_FAILED
    assert exception.status_code == 500


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_kms_decryption_exception_raised():
    """
    Test #117: KMSDecryptionException includes correct error code and status
    """
    # Arrange
    message = "KMS decryption failed"
    details = {"kms_key_id": "key123"}

    # Act
    exception = KMSDecryptionException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.KMS_DECRYPTION_FAILED
    assert exception.status_code == 500
    assert exception.details == details


# ==============================================
# S3 EXCEPTION TESTS (Tests 118-119)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_s3_upload_exception_raised():
    """
    Test #118: S3UploadException includes correct error code and status
    """
    # Arrange
    message = "S3 upload failed"
    details = {"bucket": "test-bucket", "s3_key": "file.bin"}

    # Act
    exception = S3UploadException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.S3_UPLOAD_FAILED
    assert exception.status_code == 500
    assert exception.details["bucket"] == "test-bucket"


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_s3_download_exception_raised():
    """
    Test #119: S3DownloadException includes correct error code and status
    """
    # Arrange
    message = "S3 download failed"
    details = {"s3_key": "nonexistent.bin"}

    # Act
    exception = S3DownloadException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.S3_DOWNLOAD_FAILED
    assert exception.status_code == 500


# ==============================================
# FILE VALIDATION EXCEPTION TESTS (Tests 120-122)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_file_too_large_exception_raised():
    """
    Test #120: FileTooLargeException includes correct error code and status
    """
    # Arrange
    message = "File exceeds 10MB limit"
    details = {"file_size_mb": 15.5, "max_size_mb": 10}

    # Act
    exception = FileTooLargeException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.FILE_TOO_LARGE
    assert exception.status_code == 413  # HTTP 413 Payload Too Large
    assert exception.details["file_size_mb"] == 15.5


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_invalid_file_type_exception_raised():
    """
    Test #121: InvalidFileTypeException includes correct error code and status
    """
    # Arrange
    message = "File type not allowed"
    details = {"mime_type": "application/x-executable"}

    # Act
    exception = InvalidFileTypeException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.INVALID_FILE_TYPE
    assert exception.status_code == 400


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_invalid_json_exception_raised():
    """
    Test #122: InvalidJSONException includes correct error code and status
    """
    # Arrange
    message = "Invalid JSON format"
    details = {"position": 10}

    # Act
    exception = InvalidJSONException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.INVALID_JSON_FORMAT
    assert exception.status_code == 400


# ==============================================
# ACCESS CONTROL EXCEPTION TESTS (Tests 123-125)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_unauthorized_access_exception_raised():
    """
    Test #123: UnauthorizedAccessException includes correct error code and status
    """
    # Arrange
    message = "User not authorized to access file"
    details = {"user_id": "user123", "file_id": "file456"}

    # Act
    exception = UnauthorizedAccessException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.UNAUTHORIZED_ACCESS
    assert exception.status_code == 403


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_file_not_found_exception_raised():
    """
    Test #124: FileNotFoundException includes correct error code and status
    """
    # Arrange
    message = "File not found in database"
    details = {"file_id": "nonexistent123"}

    # Act
    exception = FileNotFoundException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.FILE_NOT_FOUND
    assert exception.status_code == 404


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validation_exception_raised():
    """
    Test #125: ValidationException includes correct error code and status
    """
    # Arrange
    message = "Form data validation failed"
    details = {"field": "email", "error": "invalid_format"}

    # Act
    exception = ValidationException(message=message, details=details)

    # Assert
    assert exception.message == message
    assert exception.error_code == ErrorCode.VALIDATION_FAILED
    assert exception.status_code == 400
    assert exception.details["field"] == "email"


# ==============================================
# EXCEPTION DICTIONARY CONVERSION TEST (Bonus)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
def test_exception_to_dict_format():
    """
    Bonus Test: Exception to_dict() returns correct format
    """
    # Arrange
    exception = EncryptionException(
        message="Test error",
        details={"key": "value"}
    )

    # Act
    result = exception.to_dict()

    # Assert
    assert "error" in result
    assert result["error"]["code"] == ErrorCode.ENCRYPTION_FAILED.value
    assert result["error"]["message"] == "Test error"
    assert result["error"]["details"] == {"key": "value"}
