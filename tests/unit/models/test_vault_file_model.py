"""
ORM Tests for VaultFile Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime

from app.models.vault import VaultFile, VaultFileAccess, VaultFileStatus, CreationMode


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_table_name():
    """Test 28: Verify VaultFile model table name is 'vault_files'"""
    assert VaultFile.__tablename__ == "vault_files"


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_all_columns_exist():
    """Test 29: Verify all required columns exist in VaultFile model"""
    mapper = inspect(VaultFile)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'file_id', 'owner_user_id', 'template_id', 'creation_mode',
        'encrypted_dek', 'encrypted_form_data', 'nonce_form_data',
        'has_source_file', 'source_file_s3_key', 'source_file_nonce',
        'source_file_original_name', 'source_file_mime_type',
        'source_file_size_bytes', 'status', 'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in VaultFile model"


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_encrypted_dek_column():
    """Test 30: Verify encrypted_dek column is Text type"""
    mapper = inspect(VaultFile)
    encrypted_dek_col = mapper.columns['encrypted_dek']
    assert 'Text' in str(type(encrypted_dek_col.type)) or str(encrypted_dek_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_encrypted_form_data_column():
    """Test 31: Verify encrypted_form_data column is Text type"""
    mapper = inspect(VaultFile)
    encrypted_form_data_col = mapper.columns['encrypted_form_data']
    assert 'Text' in str(type(encrypted_form_data_col.type)) or str(encrypted_form_data_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_nonce_form_data_column():
    """Test 32: Verify nonce_form_data column is String type"""
    mapper = inspect(VaultFile)
    nonce_col = mapper.columns['nonce_form_data']
    assert 'String' in str(type(nonce_col.type)) or str(nonce_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_owner_user_id_foreign_key():
    """Test 33: Verify owner_user_id is a foreign key to users"""
    mapper = inspect(VaultFile)
    owner_user_id_col = mapper.columns['owner_user_id']

    # Check if it has foreign keys
    assert len(owner_user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(owner_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_template_id_column():
    """Test 34: Verify template_id column is String type"""
    mapper = inspect(VaultFile)
    template_id_col = mapper.columns['template_id']
    assert 'String' in str(type(template_id_col.type)) or str(template_id_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_creation_mode_check_constraint():
    """Test 35: Verify creation_mode has CHECK constraint ('manual', 'import')"""
    # Check if table args has check constraint
    assert hasattr(VaultFile, '__table_args__')

    # Check for check constraint in table args
    has_creation_mode_check = False
    for constraint in VaultFile.__table_args__:
        if hasattr(constraint, 'name') and 'creation_mode' in str(constraint):
            has_creation_mode_check = True
            break

    assert has_creation_mode_check, "creation_mode CHECK constraint not found"


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_status_column():
    """Test 36: Verify status column exists and has default"""
    mapper = inspect(VaultFile)
    status_col = mapper.columns['status']

    # Should have a default value
    assert status_col.default is not None or status_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_has_source_file_default():
    """Test 37: Verify has_source_file has default False"""
    mapper = inspect(VaultFile)
    has_source_file_col = mapper.columns['has_source_file']

    # Should have a default
    assert has_source_file_col.default is not None or has_source_file_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_owner_relationship():
    """Test 38: Verify vault.owner relationship exists"""
    mapper = inspect(VaultFile)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'owner' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_access_list_relationship():
    """Test 39: Verify vault.access_list relationship exists"""
    mapper = inspect(VaultFile)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'access_list' in relationship_names

    # Should cascade delete
    access_list_rel = mapper.relationships['access_list']
    assert 'delete-orphan' in str(access_list_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_timestamps():
    """Test 40: Verify created_at and updated_at columns exist"""
    mapper = inspect(VaultFile)
    column_names = [col.key for col in mapper.columns]

    assert 'created_at' in column_names
    assert 'updated_at' in column_names


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_repr_method():
    """Test 41: Verify VaultFile __repr__() method works"""
    vault = VaultFile(
        file_id="test123",
        owner_user_id=1,
        template_id="template1",
        creation_mode="manual",
        encrypted_dek="encrypted",
        encrypted_form_data="data",
        nonce_form_data="nonce123"
    )

    # Should not raise an error
    repr_str = repr(vault)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_vault_file_cascade_delete():
    """Test 42: Verify CASCADE delete on owner_user_id"""
    mapper = inspect(VaultFile)
    owner_user_id_col = mapper.columns['owner_user_id']

    # Get foreign key
    fk = list(owner_user_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
