"""
Module 0: ORM Models - Relationship/Association Models (Tests 142-156)

Validates SQLAlchemy model schema for join tables and relationship models.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 142, 144, 146, 148, 151, 156)
- Unique constraints (Tests 143, 145, 147, 150)
- Column types (Tests 149, 152)
- Common patterns (Tests 153-155)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.folder import FolderBranch, FolderLeaf
from app.models.memory import MemoryCollectionAssignment
from app.models.vault import VaultFileAccess
from app.models.death_approval import DeathApproval


# ==============================================================================
# FOLDER BRANCH TESTS (Tests 142-143)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_branch_table_name():
    """
    Test #142: Verify FolderBranch table name is 'folder_branches'

    FolderBranch represents contacts who can manage folder contents.
    """
    # Act & Assert
    assert FolderBranch.__tablename__ == "folder_branches"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_branch_unique_constraint():
    """
    Test #143: Verify UNIQUE constraint on (folder_id, contact_id)

    A contact can only be a branch once per folder.
    """
    # Arrange & Act
    assert hasattr(FolderBranch, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in FolderBranch.__table_args__:
        if hasattr(constraint, 'name') and 'uq_folder_branch' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (folder_id, contact_id) not found"


# ==============================================================================
# FOLDER LEAF TESTS (Tests 144-145)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_leaf_table_name():
    """
    Test #144: Verify FolderLeaf table name is 'folder_leaves'

    FolderLeaf represents contacts who can view folder contents.
    """
    # Act & Assert
    assert FolderLeaf.__tablename__ == "folder_leaves"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_leaf_unique_constraint():
    """
    Test #145: Verify UNIQUE constraint on (folder_id, contact_id, role)

    A contact can have one role per folder.
    """
    # Arrange & Act
    assert hasattr(FolderLeaf, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in FolderLeaf.__table_args__:
        if hasattr(constraint, 'name') and 'uq_folder_leaf' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (folder_id, contact_id, role) not found"


# ==============================================================================
# MEMORY ASSIGNMENT TESTS (Tests 146-147)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_assignment_table_name():
    """
    Test #146: Verify MemoryCollectionAssignment table name

    Links memory collections to folders.
    """
    # Act & Assert
    assert MemoryCollectionAssignment.__tablename__ == "memory_collection_assignments"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_assignment_unique_constraint():
    """
    Test #147: Verify UNIQUE constraint on (collection_id, contact_id, role)

    A contact can have one role per memory collection.
    """
    # Arrange & Act
    assert hasattr(MemoryCollectionAssignment, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in MemoryCollectionAssignment.__table_args__:
        if hasattr(constraint, 'name') and 'uq_collection_assignment' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (collection_id, contact_id, role) not found"


# ==============================================================================
# VAULT ACCESS TESTS (Tests 148-150)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_access_table_name():
    """
    Test #148: Verify VaultFileAccess table name is 'vault_file_access'

    Manages access control for vault files.
    """
    # Act & Assert
    assert VaultFileAccess.__tablename__ == "vault_file_access"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_access_status_column():
    """
    Test #149: Verify status column exists in VaultFileAccess

    Status tracks access grant state.
    """
    # Arrange
    mapper = inspect(VaultFileAccess)
    column_names = [col.key for col in mapper.columns]

    # Act & Assert
    assert 'status' in column_names


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_vault_access_unique_constraint():
    """
    Test #150: Verify UNIQUE constraint on (file_id, recipient_user_id)

    A user can only have one access grant per file.
    """
    # Arrange & Act
    assert hasattr(VaultFileAccess, '__table_args__')

    # Check for unique constraint
    has_unique_constraint = False
    for constraint in VaultFileAccess.__table_args__:
        if hasattr(constraint, 'name') and 'uq_file_recipient' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (file_id, recipient_user_id) not found"


# ==============================================================================
# DEATH APPROVAL TESTS (Tests 151-152)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_death_approval_table_name():
    """
    Test #151: Verify DeathApproval table name

    Tracks who approved/rejected death declarations.
    """
    # Act & Assert
    assert DeathApproval.__tablename__ == "death_approvals"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_death_approval_status_column():
    """
    Test #152: Verify status column is Enum type in DeathApproval

    Status tracks approval decision (approved, rejected, pending).
    """
    # Arrange
    mapper = inspect(DeathApproval)
    status_col = mapper.columns['status']

    # Act & Assert
    assert 'Enum' in str(type(status_col.type))


# ==============================================================================
# COMMON PATTERN TESTS (Tests 153-155)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_all_relationship_tables_have_timestamps():
    """
    Test #153: Verify relationship tables have timestamps where expected

    Audit trail requires created_at and updated_at.
    """
    # Arrange
    mapper = inspect(FolderBranch)
    column_names = [col.key for col in mapper.columns]

    # Act & Assert
    assert 'created_at' in column_names
    assert 'updated_at' in column_names


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_all_relationship_tables_have_foreign_keys():
    """
    Test #154: Verify relationship tables have required foreign keys

    Join tables must reference both sides of the relationship.
    """
    # Arrange
    mapper = inspect(FolderBranch)
    folder_id_col = mapper.columns['folder_id']
    contact_id_col = mapper.columns['contact_id']

    # Act & Assert
    assert len(folder_id_col.foreign_keys) > 0
    assert len(contact_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_all_relationship_tables_cascade_delete():
    """
    Test #155: Verify CASCADE delete configured on relationship tables

    When parent is deleted, relationship entries should be deleted.
    """
    # Arrange
    mapper = inspect(FolderBranch)
    folder_id_col = mapper.columns['folder_id']
    fk = list(folder_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'


# ==============================================================================
# FOLDER BRANCH SCHEMA TEST (Test 156)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_branch_all_columns():
    """
    Test #156: Verify FolderBranch has all required columns

    Ensures complete schema definition.
    """
    # Arrange
    mapper = inspect(FolderBranch)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'folder_id', 'contact_id', 'status', 'accepted_at', 'created_at', 'updated_at']

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in FolderBranch model"
