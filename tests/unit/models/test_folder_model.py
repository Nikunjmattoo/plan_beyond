"""
ORM Tests for Folder Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.folder import Folder, FolderBranch, FolderLeaf, FolderTrigger


@pytest.mark.unit
@pytest.mark.orm
def test_folder_table_name():
    """Test 43: Verify Folder model table name is 'folders'"""
    assert Folder.__tablename__ == "folders"


@pytest.mark.unit
@pytest.mark.orm
def test_folder_all_columns_exist():
    """Test 44: Verify all required columns exist in Folder model"""
    mapper = inspect(Folder)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'user_id', 'name', 'created_at', 'updated_at']

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Folder model"


@pytest.mark.unit
@pytest.mark.orm
def test_folder_name_column():
    """Test 45: Verify name column is Text type"""
    mapper = inspect(Folder)
    name_col = mapper.columns['name']
    assert 'Text' in str(type(name_col.type)) or str(name_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
def test_folder_user_id_foreign_key():
    """Test 46: Verify user_id is a foreign key to users"""
    mapper = inspect(Folder)
    user_id_col = mapper.columns['user_id']

    # Check if it has foreign keys
    assert len(user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_folder_user_relationship():
    """Test 47: Verify folder has relationship to user (implicit via foreign key)"""
    # This test verifies the foreign key exists which implies the relationship
    mapper = inspect(Folder)
    user_id_col = mapper.columns['user_id']
    assert len(user_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_folder_branches_relationship():
    """Test 48: Verify folder.branches relationship exists"""
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'branches' in relationship_names

    # Should cascade delete
    branches_rel = mapper.relationships['branches']
    assert 'delete-orphan' in str(branches_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_folder_leaves_relationship():
    """Test 49: Verify folder.leaves relationship exists"""
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'leaves' in relationship_names

    # Should cascade delete
    leaves_rel = mapper.relationships['leaves']
    assert 'delete-orphan' in str(leaves_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_folder_trigger_relationship():
    """Test 50: Verify folder.trigger relationship (one-to-one)"""
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'trigger' in relationship_names

    # Should be one-to-one (uselist=False)
    trigger_rel = mapper.relationships['trigger']
    assert trigger_rel.uselist is False

    # Should cascade delete
    assert 'delete-orphan' in str(trigger_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_folder_files_relationship():
    """Test 51: Verify folder.files relationship exists"""
    mapper = inspect(Folder)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'files' in relationship_names

    # Should cascade delete
    files_rel = mapper.relationships['files']
    assert 'delete-orphan' in str(files_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_folder_timestamps():
    """Test 52: Verify created_at and updated_at columns exist"""
    mapper = inspect(Folder)
    column_names = [col.key for col in mapper.columns]

    assert 'created_at' in column_names
    assert 'updated_at' in column_names


@pytest.mark.unit
@pytest.mark.orm
def test_folder_repr_method():
    """Test 53: Verify Folder __repr__() method works"""
    folder = Folder(
        user_id=1,
        name="Test Folder"
    )

    # Should not raise an error
    repr_str = repr(folder)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_folder_cascade_delete():
    """Test 54: Verify CASCADE delete on user_id"""
    mapper = inspect(Folder)
    user_id_col = mapper.columns['user_id']

    # Get foreign key
    fk = list(user_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
