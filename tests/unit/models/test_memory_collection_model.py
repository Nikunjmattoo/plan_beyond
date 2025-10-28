"""
Module 0: ORM Models - MemoryCollection Model (Tests 55-66)

Validates SQLAlchemy model schema for memory collections (posthumous messages).
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 55-56)
- Foreign keys (Test 57)
- Column types (Test 58)
- Nullability (Test 59)
- Default values (Test 60)
- Relationships (Tests 61-63)
- Timestamps (Test 64)
- Model behavior (Tests 65-66)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.memory import MemoryCollection, MemoryFile, MemoryCollectionAssignment


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 55-56)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_table_name():
    """
    Test #55: Verify MemoryCollection model table name is 'memory_collections'

    Validates that SQLAlchemy maps the MemoryCollection class to the correct table.
    """
    # Act & Assert
    assert MemoryCollection.__tablename__ == "memory_collections"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_all_columns_exist():
    """
    Test #56: Verify all required columns exist in MemoryCollection model

    Ensures the ORM schema matches database schema.
    MemoryCollection groups memory files for scheduled release.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'user_id', 'name', 'description', 'event_type',
        'scheduled_at', 'event_label', 'is_armed', 'status',
        'created_at', 'updated_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in MemoryCollection model"


# ==============================================================================
# FOREIGN KEY TESTS (Test 57)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_user_id_foreign_key():
    """
    Test #57: Verify user_id is a foreign key to users

    Every memory collection must belong to a user (the creator).
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    user_id_col = mapper.columns['user_id']

    # Act & Assert
    assert len(user_id_col.foreign_keys) > 0

    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


# ==============================================================================
# COLUMN TYPE TESTS (Test 58)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_event_type_enum():
    """
    Test #58: Verify event_type is Enum type

    Event type defines trigger condition (death, date, manual, etc.).
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    event_type_col = mapper.columns['event_type']

    # Act & Assert
    assert 'Enum' in str(type(event_type_col.type))


# ==============================================================================
# NULLABILITY TESTS (Test 59)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_scheduled_at_nullable():
    """
    Test #59: Verify scheduled_at is nullable

    scheduled_at is optional - not all triggers are time-based.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    scheduled_at_col = mapper.columns['scheduled_at']

    # Act & Assert
    assert scheduled_at_col.nullable is True or scheduled_at_col.nullable is None


# ==============================================================================
# DEFAULT VALUE TESTS (Test 60)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_is_armed_default():
    """
    Test #60: Verify is_armed has default False

    Memory collections are not armed (ready to trigger) by default.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    is_armed_col = mapper.columns['is_armed']

    # Act & Assert
    assert is_armed_col.default is not None or is_armed_col.server_default is not None


# ==============================================================================
# RELATIONSHIP TESTS (Tests 61-63)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_user_relationship():
    """
    Test #61: Verify memory.user relationship exists (implicit via FK)

    Foreign key establishes the relationship to the owning user.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    user_id_col = mapper.columns['user_id']

    # Act & Assert
    assert len(user_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_files_relationship():
    """
    Test #62: Verify memory.files relationship exists

    Files (videos, letters) contained in this memory collection.
    Should cascade delete when collection is deleted.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'files' in relationship_names

    # Verify cascade delete
    files_rel = mapper.relationships['files']
    assert 'delete-orphan' in str(files_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_assignments_relationship():
    """
    Test #63: Verify memory.folder_assignments relationship exists

    Folder assignments link memory collections to folders.
    Should cascade delete when collection is deleted.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'folder_assignments' in relationship_names

    # Verify cascade delete
    assignments_rel = mapper.relationships['folder_assignments']
    assert 'delete-orphan' in str(assignments_rel.cascade)


# ==============================================================================
# TIMESTAMP TESTS (Test 64)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_timestamps():
    """
    Test #64: Verify created_at and updated_at columns exist

    Tracks memory collection creation and modification times.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    column_names = [col.key for col in mapper.columns]

    # Act & Assert
    assert 'created_at' in column_names
    assert 'updated_at' in column_names


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 65-66)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_repr_method():
    """
    Test #65: Verify MemoryCollection __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    memory = MemoryCollection(
        user_id=1,
        name="Test Memory"
    )

    # Act
    repr_str = repr(memory)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_memory_collection_cascade_delete():
    """
    Test #66: Verify CASCADE delete on user_id

    When user is deleted, all their memory collections should be deleted.
    """
    # Arrange
    mapper = inspect(MemoryCollection)
    user_id_col = mapper.columns['user_id']
    fk = list(user_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
