"""
Module 3: Vault - Validators Tests (Tests 99-113)

Tests input validation for vault files (size, MIME type, form data).
"""
import pytest
import json
from unittest.mock import Mock

from encryption_module.validators import (
    validate_file_size,
    validate_mime_type,
    validate_form_data,
    validate_template_id,
    validate_creation_mode
)
from encryption_module.exceptions import (
    FileTooLargeException,
    InvalidFileTypeException,
    ValidationException,
    InvalidJSONException
)


# ==============================================
# FILE SIZE VALIDATION TESTS (Tests 99-101)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_file_size_within_limit():
    """
    Test #99: Files under 10MB size limit pass validation
    """
    # Arrange
    file_size = 5 * 1024 * 1024  # 5 MB
    filename = "document.pdf"

    # Act & Assert - Should not raise
    validate_file_size(file_size, filename)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_file_size_exceeds_limit():
    """
    Test #100: Files over 10MB size limit raise FileTooLargeException
    """
    # Arrange
    file_size = 11 * 1024 * 1024  # 11 MB (exceeds 10MB limit)
    filename = "large_document.pdf"

    # Act & Assert
    with pytest.raises(FileTooLargeException):
        validate_file_size(file_size, filename)


@pytest.mark.unit
@pytest.mark.vault
def test_validate_file_size_exact_limit():
    """
    Test #101: Files exactly at 10MB limit pass validation
    """
    # Arrange
    file_size = 10 * 1024 * 1024  # Exactly 10 MB
    filename = "exact_limit.pdf"

    # Act & Assert - Should not raise
    validate_file_size(file_size, filename)


# ==============================================
# MIME TYPE VALIDATION TESTS (Tests 102-104)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_mime_type_pdf():
    """
    Test #102: PDF MIME type is allowed
    """
    # Arrange
    mime_type = "application/pdf"
    filename = "document.pdf"

    # Act & Assert - Should not raise
    validate_mime_type(mime_type, filename)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_mime_type_image():
    """
    Test #103: Image MIME types are allowed
    """
    # Arrange
    image_types = ["image/jpeg", "image/png"]

    # Act & Assert - Should not raise
    for mime_type in image_types:
        validate_mime_type(mime_type, f"image.{mime_type.split('/')[-1]}")


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_mime_type_invalid():
    """
    Test #104: Invalid MIME type raises InvalidFileTypeException
    """
    # Arrange
    mime_type = "application/x-executable"
    filename = "malicious.exe"

    # Act & Assert
    with pytest.raises(InvalidFileTypeException):
        validate_mime_type(mime_type, filename)


# ==============================================
# FORM DATA VALIDATION TESTS (Tests 105-107)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_form_data_json_valid():
    """
    Test #105: Valid JSON form data passes validation
    """
    # Arrange
    form_data_dict = {
        "field1": "value1",
        "field2": "value2",
        "field3": "value3"
    }
    form_data_str = json.dumps(form_data_dict)

    # Act
    result = validate_form_data(form_data_str)

    # Assert
    assert result == form_data_dict


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_form_data_json_invalid():
    """
    Test #106: Invalid JSON raises InvalidJSONException
    """
    # Arrange
    invalid_json = "{invalid json format"

    # Act & Assert
    with pytest.raises(InvalidJSONException):
        validate_form_data(invalid_json)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_form_data_too_many_fields():
    """
    Test #107: Form data with >100 fields raises ValidationException
    """
    # Arrange
    # Create form data with 101 fields (exceeds MAX_FIELD_COUNT of 100)
    form_data_dict = {f"field{i}": f"value{i}" for i in range(101)}
    form_data_str = json.dumps(form_data_dict)

    # Act & Assert
    with pytest.raises(ValidationException):
        validate_form_data(form_data_str)


# ==============================================
# TEMPLATE ID VALIDATION TESTS (Tests 108-109)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_template_id_exists():
    """
    Test #108: Valid template ID passes validation
    """
    # Arrange
    template_id = "template123"

    # Act & Assert - Should not raise
    validate_template_id(template_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_template_id_invalid():
    """
    Test #109: Empty template ID raises ValidationException
    """
    # Arrange
    template_id = ""

    # Act & Assert
    with pytest.raises(ValidationException):
        validate_template_id(template_id)


# ==============================================
# CREATION MODE VALIDATION TESTS (Tests 110-112)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_creation_mode_manual():
    """
    Test #110: 'manual' creation mode is valid
    """
    # Arrange
    creation_mode = "manual"

    # Act & Assert - Should not raise
    validate_creation_mode(creation_mode)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_creation_mode_import():
    """
    Test #111: 'import' creation mode is valid
    """
    # Arrange
    creation_mode = "import"

    # Act & Assert - Should not raise
    validate_creation_mode(creation_mode)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_validate_creation_mode_invalid():
    """
    Test #112: Invalid creation mode raises ValidationException
    """
    # Arrange
    creation_mode = "invalid_mode"

    # Act & Assert
    with pytest.raises(ValidationException):
        validate_creation_mode(creation_mode)


# ==============================================
# ADDITIONAL VALIDATION TESTS (Test 113)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
def test_validate_form_data_non_dict_raises_exception():
    """
    Test #113: Form data that's not a dictionary raises ValidationException
    """
    # Arrange
    form_data_str = json.dumps(["array", "not", "dict"])

    # Act & Assert
    with pytest.raises(ValidationException):
        validate_form_data(form_data_str)
