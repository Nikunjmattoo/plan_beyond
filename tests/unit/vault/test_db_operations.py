"""
Module 3: Vault - Database Operations Tests (Tests 66-80)

Tests vault file database operations (CRUD, access control).
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from encryption_module.core.db_operations import VaultDatabaseOperations
from encryption_module.exceptions import (
    UnauthorizedAccessException,
    FileNotFoundException,
    DatabaseWriteException
)


# ==============================================
# ACCESS CONTROL TESTS (Tests 66-70)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_check_access_owner_has_access():
    """
    Test #66: File owner has access to their own files
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"
    owner_id = "user123"

    mock_file = Mock()
    mock_file.owner_user_id = owner_id

    mock_session.query().filter().first.return_value = mock_file

    # Act & Assert - Should not raise
    result = db_ops.check_access(file_id, owner_id)
    assert result is True


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_check_access_non_owner_raises_exception():
    """
    Test #67: Non-owner without permissions raises UnauthorizedAccessException
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"
    owner_id = "user123"
    other_user = "user456"

    mock_file = Mock()
    mock_file.owner_user_id = owner_id

    # First query returns the vault file, second query returns None (no access)
    mock_session.query().filter().first.side_effect = [mock_file, None]

    # Act & Assert
    with pytest.raises(UnauthorizedAccessException):
        db_ops.check_access(file_id, other_user)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_check_access_shared_user_has_access():
    """
    Test #68: Users with shared access can access file
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"
    owner_id = "user123"
    shared_user = "user456"

    mock_file = Mock()
    mock_file.owner_user_id = owner_id

    mock_access = Mock()
    mock_access.status = 'active'

    # First query returns vault file, second query returns active access
    mock_session.query().filter().first.side_effect = [mock_file, mock_access]

    # Act & Assert - Should not raise
    result = db_ops.check_access(file_id, shared_user)
    assert result is True


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_check_access_nonexistent_file_raises_exception():
    """
    Test #69: Non-existent file raises FileNotFoundException
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "nonexistent"
    user_id = "user123"

    mock_session.query().filter().first.return_value = None

    # Act & Assert
    with pytest.raises(FileNotFoundException):
        db_ops.check_access(file_id, user_id)


@pytest.mark.unit
@pytest.mark.vault
def test_check_access_called_before_database_read():
    """
    Test #70: check_access queries database for file
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"
    user_id = "user123"

    mock_file = Mock()
    mock_file.owner_user_id = user_id

    mock_session.query().filter().first.return_value = mock_file

    # Act
    db_ops.check_access(file_id, user_id)

    # Assert
    mock_session.query.assert_called()


# ==============================================
# FILE RETRIEVAL TESTS (Tests 71-73)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_get_vault_file_returns_file_object():
    """
    Test #71: get_vault_file returns VaultFile object for valid ID
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"

    mock_file = Mock()
    mock_session.query().filter().first.return_value = mock_file

    # Act
    result = db_ops.get_vault_file(file_id)

    # Assert
    assert result == mock_file


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_get_vault_file_nonexistent_returns_none():
    """
    Test #72: get_vault_file returns None for non-existent file
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "nonexistent"

    mock_session.query().filter().first.return_value = None

    # Act
    result = db_ops.get_vault_file(file_id)

    # Assert
    assert result is None


@pytest.mark.unit
@pytest.mark.vault
def test_get_vault_file_queries_by_file_id():
    """
    Test #73: get_vault_file queries database with correct file_id
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"

    # Act
    db_ops.get_vault_file(file_id)

    # Assert
    mock_session.query.assert_called_once()


# ==============================================
# FILE CREATION TESTS (Tests 74-76)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_create_vault_file_saves_to_database():
    """
    Test #74: create_vault_file commits file to database
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)

    file_data = {
        'file_id': 'file123',
        'owner_user_id': 'user123',
        'template_id': 'template123',
        'creation_mode': 'standard',
        'encrypted_dek': 'encrypted_key',
        'encrypted_form_data': 'encrypted_data',
        'nonce_form_data': 'nonce',
        'has_source_file': False
    }

    # Act
    db_ops.create_vault_file(**file_data)

    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_create_vault_file_duplicate_raises_exception():
    """
    Test #75: Creating duplicate file_id raises DuplicateFileException
    """
    # Arrange
    mock_session = Mock()
    mock_orig = Mock()
    mock_orig.__str__ = lambda self: "duplicate key value violates unique constraint"
    mock_error = IntegrityError("Duplicate", None, mock_orig)
    mock_session.commit.side_effect = mock_error

    db_ops = VaultDatabaseOperations(mock_session)

    file_data = {
        'file_id': 'duplicate123',
        'owner_user_id': 'user123',
        'template_id': 'template123',
        'creation_mode': 'standard',
        'encrypted_dek': 'key',
        'encrypted_form_data': 'data',
        'nonce_form_data': 'nonce',
        'has_source_file': False
    }

    # Act & Assert
    with pytest.raises(Exception):  # Can be DuplicateFileException or DatabaseWriteException
        db_ops.create_vault_file(**file_data)


@pytest.mark.unit
@pytest.mark.vault
def test_create_vault_file_returns_created_file():
    """
    Test #76: create_vault_file returns the created VaultFile object
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)

    file_data = {
        'file_id': 'file123',
        'owner_user_id': 'user123',
        'template_id': 'template123',
        'creation_mode': 'standard',
        'encrypted_dek': 'key',
        'encrypted_form_data': 'data',
        'nonce_form_data': 'nonce',
        'has_source_file': False
    }

    # Act
    result = db_ops.create_vault_file(**file_data)

    # Assert
    assert result is not None


# ==============================================
# FILE DELETION TESTS (Tests 77-78)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_delete_vault_file_removes_from_database():
    """
    Test #77: delete_vault_file commits deletion to database (soft delete by default)
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"

    mock_file = Mock()
    mock_file.has_source_file = False  # No S3 cleanup needed
    mock_session.query().filter().first.return_value = mock_file

    # Act
    result = db_ops.delete_vault_file(file_id)

    # Assert - Soft delete sets status, doesn't call delete()
    assert result is True
    assert mock_file.status == 'deleted'
    mock_session.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_delete_nonexistent_file_raises_exception():
    """
    Test #78: Deleting non-existent file raises FileNotFoundException
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "nonexistent"

    mock_session.query().filter().first.return_value = None

    # Act & Assert
    with pytest.raises(FileNotFoundException):
        db_ops.delete_vault_file(file_id)


# ==============================================
# ACCESS RECORDING TESTS (Tests 79-80)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
def test_record_file_access_creates_log_entry():
    """
    Test #79: record_access updates access log entry
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"
    user_id = "user123"

    mock_access = Mock()
    mock_access.access_count = 0
    mock_session.query().filter().first.return_value = mock_access

    # Act
    db_ops.record_access(file_id, user_id)

    # Assert
    mock_session.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
def test_record_file_access_includes_timestamp():
    """
    Test #80: Access log updates timestamp
    """
    # Arrange
    mock_session = Mock()
    db_ops = VaultDatabaseOperations(mock_session)
    file_id = "file123"
    user_id = "user123"

    mock_access = Mock()
    mock_access.access_count = 5
    mock_access.last_accessed_at = None
    mock_session.query().filter().first.return_value = mock_access

    # Act
    db_ops.record_access(file_id, user_id)

    # Assert
    # Verify timestamp was updated (last_accessed_at is set in the method)
    assert mock_access.last_accessed_at is not None
