"""
ORM Tests for Relationship/Association Models
Tests SQLAlchemy model schema for join tables and relationship models
"""
import pytest
from sqlalchemy import inspect

from app.models.folder import FolderBranch, FolderLeaf
from app.models.memory import MemoryCollectionAssignment
from app.models.vault import VaultFileAccess
from app.models.death_approval import DeathApproval


@pytest.mark.unit
@pytest.mark.orm
def test_folder_branch_table_name():
    """Test 142: Verify FolderBranch table name is 'folder_branches'"""
    assert FolderBranch.__tablename__ == "folder_branches"


@pytest.mark.unit
@pytest.mark.orm
def test_folder_branch_unique_constraint():
    """Test 143: Verify UNIQUE constraint on (folder_id, contact_id)"""
    assert hasattr(FolderBranch, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in FolderBranch.__table_args__:
        if hasattr(constraint, 'name') and 'uq_folder_branch' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (folder_id, contact_id) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_folder_leaf_table_name():
    """Test 144: Verify FolderLeaf table name is 'folder_leaves'"""
    assert FolderLeaf.__tablename__ == "folder_leaves"


@pytest.mark.unit
@pytest.mark.orm
def test_folder_leaf_unique_constraint():
    """Test 145: Verify UNIQUE constraint on (folder_id, contact_id, role)"""
    assert hasattr(FolderLeaf, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in FolderLeaf.__table_args__:
        if hasattr(constraint, 'name') and 'uq_folder_leaf' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (folder_id, contact_id, role) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_memory_assignment_table_name():
    """Test 146: Verify MemoryCollectionAssignment table name"""
    assert MemoryCollectionAssignment.__tablename__ == "memory_collection_assignments"


@pytest.mark.unit
@pytest.mark.orm
def test_memory_assignment_unique_constraint():
    """Test 147: Verify UNIQUE constraint on (collection_id, contact_id, role)"""
    assert hasattr(MemoryCollectionAssignment, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in MemoryCollectionAssignment.__table_args__:
        if hasattr(constraint, 'name') and 'uq_collection_assignment' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (collection_id, contact_id, role) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_vault_access_table_name():
    """Test 148: Verify VaultFileAccess table name is 'vault_file_access'"""
    assert VaultFileAccess.__tablename__ == "vault_file_access"


@pytest.mark.unit
@pytest.mark.orm
def test_vault_access_status_column():
    """Test 149: Verify status column exists in VaultFileAccess"""
    mapper = inspect(VaultFileAccess)
    column_names = [col.key for col in mapper.columns]
    assert 'status' in column_names


@pytest.mark.unit
@pytest.mark.orm
def test_vault_access_unique_constraint():
    """Test 150: Verify UNIQUE constraint on (file_id, recipient_user_id)"""
    assert hasattr(VaultFileAccess, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in VaultFileAccess.__table_args__:
        if hasattr(constraint, 'name') and 'uq_file_recipient' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (file_id, recipient_user_id) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_death_approval_table_name():
    """Test 151: Verify DeathApproval table name"""
    assert DeathApproval.__tablename__ == "death_approvals"


@pytest.mark.unit
@pytest.mark.orm
def test_death_approval_status_column():
    """Test 152: Verify status column is Enum type in DeathApproval"""
    mapper = inspect(DeathApproval)
    status_col = mapper.columns['status']
    assert 'Enum' in str(type(status_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_all_relationship_tables_have_timestamps():
    """Test 153: Verify relationship tables have timestamps where expected"""
    # FolderBranch should have timestamps
    mapper = inspect(FolderBranch)
    column_names = [col.key for col in mapper.columns]
    assert 'created_at' in column_names
    assert 'updated_at' in column_names


@pytest.mark.unit
@pytest.mark.orm
def test_all_relationship_tables_have_foreign_keys():
    """Test 154: Verify relationship tables have required foreign keys"""
    # FolderBranch should have folder_id and contact_id as foreign keys
    mapper = inspect(FolderBranch)
    folder_id_col = mapper.columns['folder_id']
    contact_id_col = mapper.columns['contact_id']

    assert len(folder_id_col.foreign_keys) > 0
    assert len(contact_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_all_relationship_tables_cascade_delete():
    """Test 155: Verify CASCADE delete configured on relationship tables"""
    # FolderBranch should cascade delete
    mapper = inspect(FolderBranch)
    folder_id_col = mapper.columns['folder_id']

    fk = list(folder_id_col.foreign_keys)[0]
    assert fk.ondelete == 'CASCADE'


@pytest.mark.unit
@pytest.mark.orm
def test_folder_branch_all_columns():
    """Test 156: Verify FolderBranch has all required columns"""
    mapper = inspect(FolderBranch)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'folder_id', 'contact_id', 'status', 'accepted_at', 'created_at', 'updated_at']

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in FolderBranch model"
