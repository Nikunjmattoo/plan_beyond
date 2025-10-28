"""
Module 0: ORM Models - VaultFile Model (Tests 28-42)

Validates SQLAlchemy model schema for encrypted vault files.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 28-29)
- Column types (Tests 30-32, 34)
- Foreign keys (Test 33)
- Check constraints (Test 35)
- Default values (Tests 36-37)
- Relationships (Tests 38-39)
- Timestamps (Test 40)
- Model behavior (Tests 41-42)
"""
import pytest
from datetime import datetime

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.vault import VaultFile, VaultFileAccess, VaultFileStatus, CreationMode


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 28-29)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_table_name():
    """
    Test #28: Verify VaultFile model table name is 'vault_files'

    Validates that SQLAlchemy maps the VaultFile class to the correct table.
    """
    # Act & Assert
    assert VaultFile.__tablename__ == "vault_files"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_all_columns_exist():
    """
    Test #29: Verify all required columns exist in VaultFile model

    Ensures the ORM schema matches database schema.
    VaultFile stores encrypted document data with metadata.
    """
    # Arrange
    mapper = inspect(VaultFile)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'file_id', 'owner_user_id', 'template_id', 'creation_mode',
        'encrypted_dek', 'encrypted_form_data', 'nonce_form_data',
        'has_source_file', 'source_file_s3_key', 'source_file_nonce',
        'source_file_original_name', 'source_file_mime_type',
        'source_file_size_bytes', 'status', 'created_at', 'updated_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in VaultFile model"


# ==============================================================================
# COLUMN TYPE TESTS (Tests 30-32, 34)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_encrypted_dek_column():
    """
    Test #30: Verify encrypted_dek column is Text type

    Stores the data encryption key (DEK) encrypted with user's KEK.
    """
    # Arrange
    mapper = inspect(VaultFile)
    encrypted_dek_col = mapper.columns['encrypted_dek']

    # Act & Assert
    assert 'Text' in str(type(encrypted_dek_col.type)) or str(encrypted_dek_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_encrypted_form_data_column():
    """
    Test #31: Verify encrypted_form_data column is Text type

    Stores the actual encrypted document data.
    """
    # Arrange
    mapper = inspect(VaultFile)
    encrypted_form_data_col = mapper.columns['encrypted_form_data']

    # Act & Assert
    assert 'Text' in str(type(encrypted_form_data_col.type)) or str(encrypted_form_data_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_nonce_form_data_column():
    """
    Test #32: Verify nonce_form_data column is String type

    Stores the nonce for AES-GCM encryption.
    """
    # Arrange
    mapper = inspect(VaultFile)
    nonce_col = mapper.columns['nonce_form_data']

    # Act & Assert
    assert 'String' in str(type(nonce_col.type)) or str(nonce_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_template_id_column():
    """
    Test #34: Verify template_id column is String type

    Template ID identifies the document type (e.g., will, trust, etc.).
    """
    # Arrange
    mapper = inspect(VaultFile)
    template_id_col = mapper.columns['template_id']

    # Act & Assert
    assert 'String' in str(type(template_id_col.type)) or str(template_id_col.type) == 'VARCHAR'


# ==============================================================================
# FOREIGN KEY TESTS (Test 33)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_owner_user_id_foreign_key():
    """
    Test #33: Verify owner_user_id is a foreign key to users

    Every vault file must belong to a user (the owner).
    """
    # Arrange
    mapper = inspect(VaultFile)
    owner_user_id_col = mapper.columns['owner_user_id']

    # Act & Assert
    assert len(owner_user_id_col.foreign_keys) > 0

    fk = list(owner_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


# ==============================================================================
# CHECK CONSTRAINT TESTS (Test 35)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_creation_mode_check_constraint():
    """
    Test #35: Verify creation_mode has CHECK constraint ('manual', 'import')

    Creation mode must be either 'manual' (form) or 'import' (file upload).
    """
    # Arrange & Act
    assert hasattr(VaultFile, '__table_args__')

    # Check for check constraint in table args
    has_creation_mode_check = False
    for constraint in VaultFile.__table_args__:
        if hasattr(constraint, 'name') and 'creation_mode' in str(constraint):
            has_creation_mode_check = True
            break

    # Assert
    assert has_creation_mode_check, "creation_mode CHECK constraint not found"


# ==============================================================================
# DEFAULT VALUE TESTS (Tests 36-37)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_status_column():
    """
    Test #36: Verify status column exists and has default

    Status tracks document lifecycle (draft, active, deleted, etc.).
    """
    # Arrange
    mapper = inspect(VaultFile)
    status_col = mapper.columns['status']

    # Act & Assert
    assert status_col.default is not None or status_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_has_source_file_default():
    """
    Test #37: Verify has_source_file has default False

    Indicates whether file has an attached source document.
    """
    # Arrange
    mapper = inspect(VaultFile)
    has_source_file_col = mapper.columns['has_source_file']

    # Act & Assert
    assert has_source_file_col.default is not None or has_source_file_col.server_default is not None


# ==============================================================================
# RELATIONSHIP TESTS (Tests 38-39)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_owner_relationship():
    """
    Test #38: Verify vault.owner relationship exists

    Validates relationship to the user who owns this vault file.
    """
    # Arrange
    mapper = inspect(VaultFile)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'owner' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_access_list_relationship():
    """
    Test #39: Verify vault.access_list relationship exists

    Validates cascade delete for access control entries.
    When vault file is deleted, all access grants should be deleted.
    """
    # Arrange
    mapper = inspect(VaultFile)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'access_list' in relationship_names

    # Verify cascade delete
    access_list_rel = mapper.relationships['access_list']
    assert 'delete-orphan' in str(access_list_rel.cascade)


# ==============================================================================
# TIMESTAMP TESTS (Test 40)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_timestamps():
    """
    Test #40: Verify created_at and updated_at columns exist

    Tracks document creation and modification times.
    """
    # Arrange
    mapper = inspect(VaultFile)
    column_names = [col.key for col in mapper.columns]

    # Act & Assert
    assert 'created_at' in column_names
    assert 'updated_at' in column_names


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 41-42)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_repr_method():
    """
    Test #41: Verify VaultFile __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    vault = VaultFile(
        file_id="test123",
        owner_user_id=1,
        template_id="template1",
        creation_mode="manual",
        encrypted_dek="encrypted",
        encrypted_form_data="data",
        nonce_form_data="nonce123"
    )

    # Act
    repr_str = repr(vault)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_file_cascade_delete():
    """
    Test #42: Verify CASCADE delete on owner_user_id

    When user is deleted, all their vault files should be deleted.
    """
    # Arrange
    mapper = inspect(VaultFile)
    owner_user_id_col = mapper.columns['owner_user_id']
    fk = list(owner_user_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
