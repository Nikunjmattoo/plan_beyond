"""
Module 0: ORM Models - Folder Model (Tests 43-54)

Validates SQLAlchemy model schema for user folders and sharing.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 43-44)
- Column types (Test 45)
- Foreign keys (Test 46)
- Relationships (Tests 47-51)
- Timestamps (Test 52)
- Model behavior (Tests 53-54)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.folder import Folder, FolderBranch, FolderLeaf, FolderTrigger


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 43-44)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_table_name():
    """
    Test #43: Verify Folder model table name is 'folders'

    Validates that SQLAlchemy maps the Folder class to the correct table.
    """
    # Act & Assert
    assert Folder.__tablename__ == "folders"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_all_columns_exist():
    """
    Test #44: Verify all required columns exist in Folder model

    Ensures the ORM schema matches database schema.
    Folders organize vault files for sharing.
    """
    # Arrange
    mapper = inspect(Folder)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'user_id', 'name', 'created_at', 'updated_at']

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Folder model"


# ==============================================================================
# COLUMN TYPE TESTS (Test 45)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_name_column():
    """
    Test #45: Verify name column is Text type

    Folder name can be a longer descriptive string.
    """
    # Arrange
    mapper = inspect(Folder)
    name_col = mapper.columns['name']

    # Act & Assert
    assert 'Text' in str(type(name_col.type)) or str(name_col.type) == 'TEXT'


# ==============================================================================
# FOREIGN KEY TESTS (Test 46)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_user_id_foreign_key():
    """
    Test #46: Verify user_id is a foreign key to users

    Every folder must belong to a user (the owner).
    """
    # Arrange
    mapper = inspect(Folder)
    user_id_col = mapper.columns['user_id']

    # Act & Assert
    assert len(user_id_col.foreign_keys) > 0

    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


# ==============================================================================
# RELATIONSHIP TESTS (Tests 47-51)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_user_relationship():
    """
    Test #47: Verify folder has relationship to user (implicit via foreign key)

    Foreign key establishes the relationship to the owning user.
    """
    # Arrange
    mapper = inspect(Folder)
    user_id_col = mapper.columns['user_id']

    # Act & Assert
    assert len(user_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_branches_relationship():
    """
    Test #48: Verify folder.branches relationship exists

    Branches represent contacts who can add/remove files (managers).
    Should cascade delete when folder is deleted.
    """
    # Arrange
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'branches' in relationship_names

    # Verify cascade delete
    branches_rel = mapper.relationships['branches']
    assert 'delete-orphan' in str(branches_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_leaves_relationship():
    """
    Test #49: Verify folder.leaves relationship exists

    Leaves represent contacts who can only view files (viewers).
    Should cascade delete when folder is deleted.
    """
    # Arrange
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'leaves' in relationship_names

    # Verify cascade delete
    leaves_rel = mapper.relationships['leaves']
    assert 'delete-orphan' in str(leaves_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_trigger_relationship():
    """
    Test #50: Verify folder.trigger relationship (one-to-one)

    Trigger defines when folder content should be released.
    Should be one-to-one and cascade delete.
    """
    # Arrange
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'trigger' in relationship_names

    # Verify one-to-one
    trigger_rel = mapper.relationships['trigger']
    assert trigger_rel.uselist is False

    # Verify cascade delete
    assert 'delete-orphan' in str(trigger_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_files_relationship():
    """
    Test #51: Verify folder.files relationship exists

    Files contained in this folder.
    Should cascade delete when folder is deleted.
    """
    # Arrange
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'files' in relationship_names

    # Verify cascade delete
    files_rel = mapper.relationships['files']
    assert 'delete-orphan' in str(files_rel.cascade)


# ==============================================================================
# TIMESTAMP TESTS (Test 52)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_timestamps():
    """
    Test #52: Verify created_at and updated_at columns exist

    Tracks folder creation and modification times.
    """
    # Arrange
    mapper = inspect(Folder)
    column_names = [col.key for col in mapper.columns]

    # Act & Assert
    assert 'created_at' in column_names
    assert 'updated_at' in column_names


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 53-54)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_repr_method():
    """
    Test #53: Verify Folder __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    folder = Folder(
        user_id=1,
        name="Test Folder"
    )

    # Act
    repr_str = repr(folder)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_folder_cascade_delete():
    """
    Test #54: Verify CASCADE delete on user_id

    When user is deleted, all their folders should be deleted.
    """
    # Arrange
    mapper = inspect(Folder)
    user_id_col = mapper.columns['user_id']
    fk = list(user_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
