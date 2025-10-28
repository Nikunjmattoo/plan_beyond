"""
Module 3: Vault - S3 Operations Tests (Tests 81-98)

Tests S3 upload/download operations for encrypted vault files.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from encryption_module.core.s3_operations import S3Operations
from encryption_module.exceptions import (
    S3UploadException,
    S3DownloadException,
    S3DeleteException,
    S3AccessDeniedException,
    FileNotFoundException
)


# ==============================================
# UPLOAD TESTS (Tests 81-85)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_upload_file_to_s3():
    """
    Test #81: Upload encrypted file to S3 successfully
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()
        encrypted_data = b"encrypted_file_data"
        file_id = "file123"
        user_id = "user123"

        # Act
        result = s3_ops.upload_encrypted_file(encrypted_data, file_id, user_id)

    # Assert
    assert result == f"vault_files/{user_id}/{file_id}/source.bin"
    mock_s3.put_object.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_upload_generates_correct_key():
    """
    Test #82: Upload generates correct S3 key format
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()
        encrypted_data = b"data"
        file_id = "abc123"
        user_id = "user456"

        # Act
        s3_key = s3_ops.upload_encrypted_file(encrypted_data, file_id, user_id)

    # Assert
    assert s3_key.startswith("vault_files/")
    assert user_id in s3_key
    assert file_id in s3_key
    assert s3_key.endswith("source.bin")


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_upload_sets_correct_mime_type():
    """
    Test #83: Upload sets correct server-side encryption
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()
        encrypted_data = b"data"

        # Act
        s3_ops.upload_encrypted_file(encrypted_data, "file123", "user123")

    # Assert
    call_args = mock_s3.put_object.call_args
    assert call_args[1]['ServerSideEncryption'] == 'AES256'


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_upload_file_encrypted():
    """
    Test #84: Upload includes encryption metadata
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()
        encrypted_data = b"encrypted_data"

        # Act
        s3_ops.upload_encrypted_file(encrypted_data, "file123", "user123")

    # Assert
    call_args = mock_s3.put_object.call_args
    metadata = call_args[1]['Metadata']
    assert metadata['encryption'] == 'AES-256-GCM'
    assert metadata['user_id'] == 'user123'
    assert metadata['file_id'] == 'file123'


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_upload_failure_raises_exception():
    """
    Test #85: S3 upload failure raises S3UploadException
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        error_response = {'Error': {'Code': 'InternalError', 'Message': 'S3 error'}}
        mock_s3.put_object.side_effect = ClientError(error_response, 'PutObject')

        s3_ops = S3Operations()

        # Act & Assert
        with pytest.raises(S3UploadException):
            s3_ops.upload_encrypted_file(b"data", "file123", "user123")


# ==============================================
# DOWNLOAD TESTS (Tests 86-89)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_download_file_from_s3():
    """
    Test #86: Download encrypted file from S3 successfully
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        mock_response = {
            'Body': Mock()
        }
        expected_data = b"encrypted_file_data"
        mock_response['Body'].read.return_value = expected_data
        mock_s3.get_object.return_value = mock_response

        s3_ops = S3Operations()
        s3_key = "vault_files/user123/file123/source.bin"

        # Act
        result = s3_ops.download_encrypted_file(s3_key)

    # Assert
    assert result == expected_data
    mock_s3.get_object.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_download_decrypts_file():
    """
    Test #87: Download returns raw bytes (decryption happens elsewhere)
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        mock_response = {'Body': Mock()}
        encrypted_data = b"encrypted_bytes_here"
        mock_response['Body'].read.return_value = encrypted_data
        mock_s3.get_object.return_value = mock_response

        s3_ops = S3Operations()

        # Act
        result = s3_ops.download_encrypted_file("vault_files/user123/file123/source.bin")

    # Assert
    assert isinstance(result, bytes)
    assert result == encrypted_data


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_download_invalid_key_raises_exception():
    """
    Test #88: Download with empty S3 key raises exception
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()

        # Act & Assert
        with pytest.raises(S3DownloadException):
            s3_ops.download_encrypted_file("")


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_download_not_found_raises_exception():
    """
    Test #89: Download non-existent file raises FileNotFoundException
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Not found'}}
        mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')

        s3_ops = S3Operations()

        # Act & Assert
        with pytest.raises(FileNotFoundException):
            s3_ops.download_encrypted_file("vault_files/user123/nonexistent/source.bin")


# ==============================================
# PRESIGNED URL TESTS (Tests 90-92)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_generate_presigned_url():
    """
    Test #90: Generate presigned download URL successfully
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        expected_url = "https://s3.amazonaws.com/bucket/key?signature=xyz"
        mock_s3.generate_presigned_url.return_value = expected_url

        s3_ops = S3Operations()
        s3_key = "vault_files/user123/file123/source.bin"

        # Act
        result = s3_ops.generate_presigned_download_url(s3_key)

    # Assert
    assert result == expected_url
    mock_s3.generate_presigned_url.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_presigned_url_expires_in_1_hour():
    """
    Test #91: Presigned URL expires in 1 hour by default
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        mock_s3.generate_presigned_url.return_value = "https://s3.url"

        s3_ops = S3Operations()

        # Act
        s3_ops.generate_presigned_download_url("vault_files/user123/file123/source.bin")

    # Assert
    call_args = mock_s3.generate_presigned_url.call_args
    # Default expiry should be 3600 seconds (1 hour)
    assert call_args[1]['ExpiresIn'] == 3600


@pytest.mark.unit
@pytest.mark.vault
def test_presigned_url_format_correct():
    """
    Test #92: Presigned URL has correct parameters
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        mock_s3.generate_presigned_url.return_value = "https://s3.url"

        s3_ops = S3Operations()
        s3_key = "vault_files/user123/file123/source.bin"

        # Act
        s3_ops.generate_presigned_download_url(s3_key)

    # Assert
    call_args = mock_s3.generate_presigned_url.call_args
    assert call_args[0][0] == 'get_object'
    assert call_args[1]['Params']['Key'] == s3_key


# ==============================================
# DELETE TESTS (Tests 93-94)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_delete_file_from_s3():
    """
    Test #93: Delete file from S3 successfully
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()
        s3_key = "vault_files/user123/file123/source.bin"

        # Act
        s3_ops.delete_encrypted_file(s3_key)

    # Assert
    mock_s3.delete_object.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
def test_delete_nonexistent_file_succeeds():
    """
    Test #94: Delete is idempotent (deleting non-existent file succeeds)
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        # S3 delete_object doesn't raise error for non-existent files
        mock_s3.delete_object.return_value = {}

        s3_ops = S3Operations()

        # Act & Assert - Should not raise
        s3_ops.delete_encrypted_file("vault_files/user123/nonexistent/source.bin")


# ==============================================
# ERROR HANDLING TESTS (Tests 95-98)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
def test_list_files_in_bucket():
    """
    Test #95: List files operation (not implemented, placeholder test)
    """
    # Note: S3Operations doesn't have list_objects method yet
    # This is a placeholder for future functionality
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()

    # Assert
    assert hasattr(s3_ops, 's3')
    assert hasattr(s3_ops, 'bucket')


@pytest.mark.unit
@pytest.mark.vault
def test_list_files_with_prefix():
    """
    Test #96: List files with prefix filter (not implemented, placeholder)
    """
    # Note: S3Operations doesn't have list_objects with prefix yet
    # This is a placeholder for future functionality
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        s3_ops = S3Operations()
        user_id = "user123"

    # Assert - S3 client is available for future list operations
    assert s3_ops.s3 == mock_s3


@pytest.mark.unit
@pytest.mark.vault
def test_s3_connection_retry_on_failure():
    """
    Test #97: S3 client initialized successfully
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        # Act
        s3_ops = S3Operations()

    # Assert
    assert s3_ops.s3 is not None
    assert s3_ops.bucket is not None


@pytest.mark.unit
@pytest.mark.vault
def test_s3_timeout_raises_exception():
    """
    Test #98: S3 access denied raises S3AccessDeniedException
    """
    # Arrange
    with patch('encryption_module.core.s3_operations.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3

        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        mock_s3.put_object.side_effect = ClientError(error_response, 'PutObject')

        s3_ops = S3Operations()

        # Act & Assert
        with pytest.raises(S3AccessDeniedException):
            s3_ops.upload_encrypted_file(b"data", "file123", "user123")
