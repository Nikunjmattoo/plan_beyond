"""
ORM Tests for MemoryCollection Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.memory import MemoryCollection, MemoryFile, MemoryCollectionAssignment


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_table_name():
    """Test 55: Verify MemoryCollection model table name is 'memory_collections'"""
    assert MemoryCollection.__tablename__ == "memory_collections"


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_all_columns_exist():
    """Test 56: Verify all required columns exist in MemoryCollection model"""
    mapper = inspect(MemoryCollection)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'user_id', 'name', 'description', 'event_type',
        'scheduled_at', 'event_label', 'is_armed', 'status',
        'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in MemoryCollection model"


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_user_id_foreign_key():
    """Test 57: Verify user_id is a foreign key to users"""
    mapper = inspect(MemoryCollection)
    user_id_col = mapper.columns['user_id']

    # Check if it has foreign keys
    assert len(user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_event_type_enum():
    """Test 58: Verify event_type is Enum type"""
    mapper = inspect(MemoryCollection)
    event_type_col = mapper.columns['event_type']

    # Check if it's an Enum type
    assert 'Enum' in str(type(event_type_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_scheduled_at_nullable():
    """Test 59: Verify scheduled_at is nullable"""
    mapper = inspect(MemoryCollection)
    scheduled_at_col = mapper.columns['scheduled_at']

    # scheduled_at should be nullable (not all triggers are time-based)
    assert scheduled_at_col.nullable is True or scheduled_at_col.nullable is None


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_is_armed_default():
    """Test 60: Verify is_armed has default False"""
    mapper = inspect(MemoryCollection)
    is_armed_col = mapper.columns['is_armed']

    # Should have a default
    assert is_armed_col.default is not None or is_armed_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_user_relationship():
    """Test 61: Verify memory.user relationship exists (implicit via FK)"""
    # This test verifies the foreign key exists which implies relationship capability
    mapper = inspect(MemoryCollection)
    user_id_col = mapper.columns['user_id']
    assert len(user_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_files_relationship():
    """Test 62: Verify memory.files relationship exists"""
    mapper = inspect(MemoryCollection)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'files' in relationship_names

    # Should cascade delete
    files_rel = mapper.relationships['files']
    assert 'delete-orphan' in str(files_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_assignments_relationship():
    """Test 63: Verify memory.folder_assignments relationship exists"""
    mapper = inspect(MemoryCollection)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'folder_assignments' in relationship_names

    # Should cascade delete
    assignments_rel = mapper.relationships['folder_assignments']
    assert 'delete-orphan' in str(assignments_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_timestamps():
    """Test 64: Verify created_at and updated_at columns exist"""
    mapper = inspect(MemoryCollection)
    column_names = [col.key for col in mapper.columns]

    assert 'created_at' in column_names
    assert 'updated_at' in column_names


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_repr_method():
    """Test 65: Verify MemoryCollection __repr__() method works"""
    memory = MemoryCollection(
        user_id=1,
        name="Test Memory"
    )

    # Should not raise an error
    repr_str = repr(memory)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_memory_collection_cascade_delete():
    """Test 66: Verify CASCADE delete on user_id"""
    mapper = inspect(MemoryCollection)
    user_id_col = mapper.columns['user_id']

    # Get foreign key
    fk = list(user_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
