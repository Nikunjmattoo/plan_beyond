"""
Module 3: Vault - Vault Decryptor Tests (Tests 46-65)

Tests high-level vault file decryption orchestration.
"""
import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from encryption_module.core.vault_decryptor import decrypt_vault_file, get_decryption_metadata, DecryptedVaultData, DecryptionMetadata
from encryption_module.exceptions import (
    UnauthorizedAccessException,
    FileNotFoundException,
    DecryptionException,
    InvalidJSONException
)


# Mock vault file structure
@dataclass
class MockVaultFile:
    file_id: str
    encrypted_dek: str
    encrypted_form_data: str
    nonce_form_data: str
    has_source_file: bool
    owner_user_id: str = "user123"
    source_file_s3_key: str = None
    source_file_nonce: str = None
    source_file_original_name: str = None
    source_file_mime_type: str = None


# ==============================================
# AUTHORIZATION TESTS (Tests 46-49)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_unauthorized_access_raises_exception():
    """
    Test #46: Unauthorized access raises UnauthorizedAccessException
    """
    # Arrange
    file_id = "file123"
    user_id = "unauthorized_user"

    mock_db = Mock()
    mock_db.check_access.side_effect = UnauthorizedAccessException("Access denied")

    # Act & Assert
    with pytest.raises(UnauthorizedAccessException):
        decrypt_vault_file(file_id, user_id, mock_db)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_not_found_raises_exception():
    """
    Test #47: Non-existent file raises FileNotFoundException
    """
    # Arrange
    file_id = "nonexistent"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None
    mock_db.get_vault_file.return_value = None

    # Act & Assert
    with pytest.raises(FileNotFoundException):
        decrypt_vault_file(file_id, user_id, mock_db)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_checks_authorization_before_decryption():
    """
    Test #48: Authorization is checked before any decryption
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.side_effect = UnauthorizedAccessException("Access denied")

    # Act & Assert
    with pytest.raises(UnauthorizedAccessException):
        decrypt_vault_file(file_id, user_id, mock_db)

    # Verify check_access was called
    mock_db.check_access.assert_called_once_with(file_id, user_id)
    # Verify get_vault_file was NOT called (failed before that)
    mock_db.get_vault_file.assert_not_called()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_file_not_found_during_check_access():
    """
    Test #49: FileNotFoundException during check_access is propagated
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.side_effect = FileNotFoundException("File not found")

    # Act & Assert
    with pytest.raises(FileNotFoundException):
        decrypt_vault_file(file_id, user_id, mock_db)


# ==============================================
# FORM DATA DECRYPTION TESTS (Tests 50-55)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_decrypts_form_data_successfully():
    """
    Test #50: Form data is decrypted successfully
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"
    form_data_dict = {"name": "John", "email": "john@example.com"}

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = json.dumps(form_data_dict).encode('utf-8')

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db)

    # Assert
    assert result.form_data == form_data_dict
    assert result.has_source_file is False


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_invalid_base64_dek_raises_exception():
    """
    Test #51: Invalid base64 encoded DEK raises DecryptionException
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek="invalid_base64!!!",
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    # Act & Assert
    with pytest.raises(DecryptionException):
        decrypt_vault_file(file_id, user_id, mock_db)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_invalid_json_raises_exception():
    """
    Test #52: Invalid JSON in decrypted form data raises InvalidJSONException
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = b'not valid json{{'

        # Act & Assert
        with pytest.raises(InvalidJSONException):
            decrypt_vault_file(file_id, user_id, mock_db)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_decrypts_with_correct_dek():
    """
    Test #53: Form data is decrypted with DEK from KMS
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"
    plaintext_dek = b'plaintext_key_32_bytes_long!!!!'

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek_from_kms').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = plaintext_dek
        mock_crypto.decrypt_data.return_value = json.dumps({"field": "value"}).encode()

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db)

    # Assert
    # Verify decrypt_data was called with the decrypted DEK
    call_args = mock_crypto.decrypt_data.call_args
    assert call_args[0][1] == plaintext_dek


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_returns_decrypted_vault_data_type():
    """
    Test #54: Result is DecryptedVaultData dataclass instance
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = json.dumps({"test": "data"}).encode()

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db)

    # Assert
    assert isinstance(result, DecryptedVaultData)
    assert hasattr(result, 'form_data')
    assert hasattr(result, 'has_source_file')


@pytest.mark.unit
@pytest.mark.vault
def test_decrypt_vault_file_unicode_in_form_data():
    """
    Test #55: Unicode characters in form data are preserved
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"
    form_data_dict = {"name": "José", "city": "São Paulo", "emoji": "🔥"}

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = json.dumps(form_data_dict).encode('utf-8')

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db)

    # Assert
    assert result.form_data == form_data_dict


# ==============================================
# SOURCE FILE DECRYPTION TESTS (Tests 56-60)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_with_source_file():
    """
    Test #56: Source file is decrypted when decrypt_source_file=True
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"
    source_file_data = b"PDF file content"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=True,
        source_file_s3_key="s3://bucket/file",
        source_file_nonce=base64.b64encode(b'file_nonce12').decode(),
        source_file_original_name="document.pdf",
        source_file_mime_type="application/pdf"
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_decryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.side_effect = [
            json.dumps({"field": "value"}).encode(),  # Form data
            source_file_data  # Source file
        ]

        mock_s3 = MockS3.return_value
        mock_s3.download_encrypted_file.return_value = b'encrypted_file_data'

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db, decrypt_source_file=True)

    # Assert
    assert result.has_source_file is True
    assert result.source_file_data == source_file_data
    assert result.source_file_mime_type == "application/pdf"


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_without_source_file_flag():
    """
    Test #57: Source file NOT decrypted when decrypt_source_file=False
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=True,
        source_file_s3_key="s3://bucket/file"
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_decryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = json.dumps({"field": "value"}).encode()

        mock_s3 = MockS3.return_value

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db, decrypt_source_file=False)

    # Assert
    assert result.source_file_data is None
    # S3 should NOT be called
    mock_s3.download_encrypted_file.assert_not_called()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_no_source_file_returns_none():
    """
    Test #58: Files without source_file return source_file_data=None
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = json.dumps({"field": "value"}).encode()

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db, decrypt_source_file=True)

    # Assert
    assert result.has_source_file is False
    assert result.source_file_data is None


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_source_file_uses_same_dek():
    """
    Test #59: Source file is decrypted with same DEK as form data
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"
    plaintext_dek = b'plaintext_key_32_bytes_long!!!!'

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=True,
        source_file_s3_key="s3://bucket/file",
        source_file_nonce=base64.b64encode(b'file_nonce12').decode()
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_decryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = plaintext_dek
        mock_crypto.decrypt_data.return_value = json.dumps({"field": "value"}).encode()

        mock_s3 = MockS3.return_value
        mock_s3.download_encrypted_file.return_value = b'encrypted_file'

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db, decrypt_source_file=True)

    # Assert
    # Both decrypt_data calls should use same DEK
    assert mock_crypto.decrypt_data.call_count == 2
    call1_key = mock_crypto.decrypt_data.call_args_list[0][0][1]
    call2_key = mock_crypto.decrypt_data.call_args_list[1][0][1]
    assert call1_key == call2_key == plaintext_dek


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_vault_file_source_file_uses_different_nonce():
    """
    Test #60: Source file uses different nonce than form data
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    form_nonce = b'form_nonce12'
    file_nonce = b'file_nonce12'

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(form_nonce).decode(),
        has_source_file=True,
        source_file_s3_key="s3://bucket/file",
        source_file_nonce=base64.b64encode(file_nonce).decode()
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_decryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data.return_value = json.dumps({"field": "value"}).encode()

        mock_s3 = MockS3.return_value
        mock_s3.download_encrypted_file.return_value = b'encrypted_file'

        # Act
        result = decrypt_vault_file(file_id, user_id, mock_db, decrypt_source_file=True)

    # Assert
    # Check that nonces are different
    assert mock_crypto.decrypt_data.call_count == 2
    nonce1 = mock_crypto.decrypt_data.call_args_list[0][0][2]
    nonce2 = mock_crypto.decrypt_data.call_args_list[1][0][2]
    assert nonce1 != nonce2
    assert nonce1 == form_nonce
    assert nonce2 == file_nonce


# ==============================================
# DECRYPTION METADATA TESTS (Tests 61-65)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_get_decryption_metadata_returns_metadata_for_frontend():
    """
    Test #61: get_decryption_metadata returns metadata for client-side decryption
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek_from_kms').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        plaintext_dek = b'plaintext_key_32_bytes_long!!!!'
        mock_crypto.decrypt_data_key.return_value = plaintext_dek

        # Act
        result = get_decryption_metadata(file_id, user_id, mock_db)

    # Assert
    assert isinstance(result, DecryptionMetadata)
    assert result.encryption_key == base64.b64encode(plaintext_dek).decode()
    assert result.encrypted_form_data == vault_file.encrypted_form_data
    assert result.nonce_form_data == vault_file.nonce_form_data


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.skip(reason="get_decryption_metadata function signature needs verification")
def test_get_decryption_metadata_includes_s3_presigned_url():
    """
    Test #62: Metadata includes presigned S3 URL for source file
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=True,
        source_file_s3_key="s3://bucket/encrypted_file",
        source_file_nonce=base64.b64encode(b'file_nonce12').decode(),
        source_file_original_name="document.pdf",
        source_file_mime_type="application/pdf"
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto, \
         patch('encryption_module.core.vault_decryptor.S3Operations') as MockS3:

        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'

        mock_s3 = MockS3.return_value
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned_url"

        # Act
        result = get_decryption_metadata(file_id, user_id, mock_db)

    # Assert
    assert result.has_source_file is True
    assert result.source_file_s3_url == "https://s3.amazonaws.com/presigned_url"
    assert result.source_file_nonce == vault_file.source_file_nonce


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_get_decryption_metadata_unauthorized_raises_exception():
    """
    Test #63: Unauthorized access to metadata raises UnauthorizedAccessException
    """
    # Arrange
    file_id = "file123"
    user_id = "unauthorized"

    mock_db = Mock()
    mock_db.check_access.side_effect = UnauthorizedAccessException("Access denied")

    # Act & Assert
    with pytest.raises(UnauthorizedAccessException):
        get_decryption_metadata(file_id, user_id, mock_db)


@pytest.mark.unit
@pytest.mark.vault
def test_get_decryption_metadata_without_source_file():
    """
    Test #64: Metadata for files without source file has None values
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = b'plaintext_key_32_bytes_long!!!!'

        # Act
        result = get_decryption_metadata(file_id, user_id, mock_db)

    # Assert
    assert result.has_source_file is False
    assert result.source_file_s3_url is None
    assert result.source_file_nonce is None


@pytest.mark.unit
@pytest.mark.vault
def test_get_decryption_metadata_decrypts_dek_via_kms():
    """
    Test #65: Metadata includes DEK decrypted via KMS
    """
    # Arrange
    file_id = "file123"
    user_id = "user123"
    plaintext_dek = b'decrypted_key_from_kms_32byte'

    mock_db = Mock()
    mock_db.check_access.return_value = None

    vault_file = MockVaultFile(
        file_id=file_id,
        encrypted_dek=base64.b64encode(b'kms_encrypted_dek').decode(),
        encrypted_form_data=base64.b64encode(b'encrypted_form').decode(),
        nonce_form_data=base64.b64encode(b'nonce_12byte').decode(),
        has_source_file=False
    )
    mock_db.get_vault_file.return_value = vault_file

    with patch('encryption_module.core.vault_decryptor.CryptoEngine') as MockCrypto:
        mock_crypto = MockCrypto.return_value
        mock_crypto.decrypt_data_key.return_value = plaintext_dek

        # Act
        result = get_decryption_metadata(file_id, user_id, mock_db)

    # Assert
    # Verify DEK was decrypted via KMS
    mock_crypto.decrypt_data_key.assert_called_once()
    # Verify metadata contains the plaintext DEK (base64 encoded)
    assert base64.b64decode(result.encryption_key) == plaintext_dek
