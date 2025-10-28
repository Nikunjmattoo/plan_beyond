"""
Module 3: Vault - Vault Encryptor Tests (Tests 26-45)

Tests high-level vault file encryption orchestration.
"""
import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from encryption_module.core.vault_encryptor import encrypt_vault_file, EncryptedVaultResult
from encryption_module.exceptions import (
    ValidationException,
    EncryptionException,
    InvalidJSONException
)


# ==============================================
# INPUT VALIDATION TESTS (Tests 26-32)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_empty_form_data_raises_exception():
    """
    Test #26: Empty form_data raises ValidationException
    """
    # Arrange
    form_data = {}
    user_id = "user123"

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, None, None, None, user_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_none_form_data_raises_exception():
    """
    Test #27: None form_data raises ValidationException
    """
    # Arrange
    form_data = None
    user_id = "user123"

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, None, None, None, user_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_empty_user_id_raises_exception():
    """
    Test #28: Empty user_id raises ValidationException
    """
    # Arrange
    form_data = {"field1": "value1"}
    user_id = ""

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, None, None, None, user_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_missing_mime_type_raises_exception():
    """
    Test #29: Source file without MIME type raises ValidationException
    """
    # Arrange
    form_data = {"field1": "value1"}
    user_id = "user123"
    source_file = b"file content"

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, source_file, "test.pdf", None, user_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_invalid_creation_mode_raises_exception():
    """
    Test #30: Invalid creation_mode raises ValidationException
    """
    # Arrange
    form_data = {"field1": "value1"}
    user_id = "user123"

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, None, None, None, user_id, creation_mode="invalid")


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_zero_byte_file_raises_exception():
    """
    Test #31: Zero-byte source file raises ValidationException
    """
    # Arrange
    form_data = {"field1": "value1"}
    user_id = "user123"
    source_file = b""

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, source_file, "empty.pdf", "application/pdf", user_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_zero_byte_bytesio_raises_exception():
    """
    Test #32: Zero-byte BytesIO source file raises ValidationException
    """
    # Arrange
    form_data = {"field1": "value1"}
    user_id = "user123"
    source_file = BytesIO(b"")

    # Act & Assert
    with pytest.raises(ValidationException):
        encrypt_vault_file(form_data, source_file, "empty.pdf", "application/pdf", user_id)


# ==============================================
# FORM DATA ENCRYPTION TESTS (Tests 33-37)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_encrypts_form_data_successfully():
    """
    Test #33: Form data is encrypted and result contains encrypted form data
    """
    # Arrange
    form_data = {"name": "John", "email": "john@example.com"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert result.encrypted_form_data is not None
    assert isinstance(result.encrypted_form_data, str)
    # Should be base64 encoded
    assert base64.b64decode(result.encrypted_form_data) == b'encrypted_form_data'


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_calls_encrypt_with_json_serialized_data():
    """
    Test #34: Form data is JSON serialized before encryption
    """
    # Arrange
    form_data = {"name": "John", "age": 30}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    # Check that encrypt_data was called with JSON bytes
    call_args = mock_crypto.encrypt_data.call_args_list
    # First call is for form data
    first_call = call_args[0]
    encrypted_data = first_call[0][0]
    # Verify it's valid JSON
    parsed = json.loads(encrypted_data.decode('utf-8'))
    assert parsed == form_data


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_non_serializable_form_data_raises_exception():
    """
    Test #35: Non-JSON-serializable form data raises InvalidJSONException
    """
    # Arrange
    form_data = {"function": lambda x: x}  # Functions can't be serialized
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')

        # Act & Assert
        with pytest.raises(InvalidJSONException):
            encrypt_vault_file(form_data, None, None, None, user_id)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_generates_unique_file_id():
    """
    Test #36: Each encryption generates unique file_id
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result1 = encrypt_vault_file(form_data, None, None, None, user_id)
        result2 = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert result1.file_id != result2.file_id


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_file_id_is_16_char_hex():
    """
    Test #37: File ID is 16 character hexadecimal string
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert len(result.file_id) == 16
    # Should be valid hex
    int(result.file_id, 16)  # Raises ValueError if not hex


# ==============================================
# SOURCE FILE ENCRYPTION TESTS (Tests 38-42)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_with_source_file_bytes():
    """
    Test #38: Source file (bytes) is encrypted and uploaded to S3
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"
    source_file = b"PDF file content here"
    filename = "document.pdf"
    mime_type = "application/pdf"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_encryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_data'

        mock_s3 = MockS3.return_value
        mock_s3.upload_encrypted_file.return_value = "s3://bucket/path/file"

        # Act
        result = encrypt_vault_file(form_data, source_file, filename, mime_type, user_id)

    # Assert
    assert result.has_source_file is True
    assert result.source_file_s3_key == "s3://bucket/path/file"
    assert result.source_file_mime_type == mime_type
    assert result.source_file_size_bytes == len(source_file)
    assert result.source_file_nonce is not None


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_with_source_file_bytesio():
    """
    Test #39: Source file (BytesIO) is encrypted and uploaded to S3
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"
    file_content = b"Image file content"
    source_file = BytesIO(file_content)
    filename = "photo.jpg"
    mime_type = "image/jpeg"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_encryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_data'

        mock_s3 = MockS3.return_value
        mock_s3.upload_encrypted_file.return_value = "s3://bucket/path/file"

        # Act
        result = encrypt_vault_file(form_data, source_file, filename, mime_type, user_id)

    # Assert
    assert result.has_source_file is True
    assert result.source_file_s3_key == "s3://bucket/path/file"
    assert result.source_file_size_bytes == len(file_content)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_without_source_file():
    """
    Test #40: Encryption without source file (manual mode)
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert result.has_source_file is False
    assert result.source_file_s3_key is None
    assert result.source_file_nonce is None
    assert result.source_file_mime_type is None
    assert result.source_file_size_bytes is None


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_encrypts_source_file_with_same_dek():
    """
    Test #41: Source file is encrypted with same DEK as form data
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"
    source_file = b"File content"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_encryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        plaintext_dek = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.generate_data_key.return_value = (plaintext_dek, b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_data'

        mock_s3 = MockS3.return_value
        mock_s3.upload_encrypted_file.return_value = "s3://bucket/path/file"

        # Act
        result = encrypt_vault_file(form_data, source_file, "file.pdf", "application/pdf", user_id)

    # Assert
    # Check that encrypt_data was called twice (form + file) with same key
    assert mock_crypto.encrypt_data.call_count == 2
    call1_key = mock_crypto.encrypt_data.call_args_list[0][0][1]
    call2_key = mock_crypto.encrypt_data.call_args_list[1][0][1]
    assert call1_key == call2_key == plaintext_dek


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_source_file_uses_different_nonce():
    """
    Test #42: Source file uses different nonce than form data
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"
    source_file = b"File content"

    nonce_counter = [0]
    def mock_nonce():
        nonce_counter[0] += 1
        return f"nonce_{nonce_counter[0]}".encode().ljust(12, b'0')

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_encryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.side_effect = mock_nonce
        mock_crypto.encrypt_data.return_value = b'encrypted_data'

        mock_s3 = MockS3.return_value
        mock_s3.upload_encrypted_file.return_value = "s3://bucket/path/file"

        # Act
        result = encrypt_vault_file(form_data, source_file, "file.pdf", "application/pdf", user_id)

    # Assert
    # Should have called generate_nonce twice (once for form, once for file)
    assert mock_crypto.generate_nonce.call_count == 2
    # Nonces should be different
    assert mock_crypto.encrypt_data.call_count == 2
    nonce1 = mock_crypto.encrypt_data.call_args_list[0][0][2]
    nonce2 = mock_crypto.encrypt_data.call_args_list[1][0][2]
    assert nonce1 != nonce2


# ==============================================
# RESULT STRUCTURE TESTS (Tests 43-45)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_result_contains_encrypted_dek():
    """
    Test #43: Result contains base64-encoded encrypted DEK
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        encrypted_dek = b'encrypted_dek_from_kms'
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', encrypted_dek)
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert result.encrypted_dek is not None
    # Should be base64 encoded
    decoded = base64.b64decode(result.encrypted_dek)
    assert decoded == encrypted_dek


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_result_contains_nonce():
    """
    Test #44: Result contains base64-encoded nonce for form data
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        nonce = b'nonce_12byte'
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = nonce
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert result.nonce_form_data is not None
    # Should be base64 encoded
    decoded = base64.b64decode(result.nonce_form_data)
    assert decoded == nonce


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_vault_file_result_is_encrypted_vault_result_type():
    """
    Test #45: Result is EncryptedVaultResult dataclass instance
    """
    # Arrange
    form_data = {"field": "value"}
    user_id = "user123"

    with patch('encryption_module.core.vault_encryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.generate_data_key.return_value = (b'plaintext_key_32_bytes_long!!!!', b'encrypted_dek')
        mock_crypto.generate_nonce.return_value = b'nonce_12byte'
        mock_crypto.encrypt_data.return_value = b'encrypted_form_data'

        # Act
        result = encrypt_vault_file(form_data, None, None, None, user_id)

    # Assert
    assert isinstance(result, EncryptedVaultResult)
    assert hasattr(result, 'file_id')
    assert hasattr(result, 'encrypted_dek')
    assert hasattr(result, 'encrypted_form_data')
    assert hasattr(result, 'nonce_form_data')
    assert hasattr(result, 'has_source_file')
