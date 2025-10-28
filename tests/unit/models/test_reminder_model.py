"""
Module 0: ORM Models - Reminder Model (Tests 124-133)

Validates SQLAlchemy model schema for reminder system.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 124-125)
- Foreign keys (Tests 126-127)
- Column types (Test 128)
- Column presence (Tests 129-130)
- Relationships (Tests 131-132)
- Model behavior (Test 133)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.reminder import Reminder


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 124-125)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_table_name():
    """
    Test #124: Verify Reminder model table name is 'reminders'

    Validates that SQLAlchemy maps the Reminder class to the correct table.
    """
    # Act & Assert
    assert Reminder.__tablename__ == "reminders"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_all_columns_exist():
    """
    Test #125: Verify all required columns exist in Reminder model

    Ensures the ORM schema matches database schema.
    Reminders notify users about upcoming dates in their documents.
    """
    # Arrange
    mapper = inspect(Reminder)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'user_id', 'vault_file_id', 'field_name', 'reminder_category',
        'trigger_date', 'reminder_date', 'title', 'message', 'urgency_level',
        'status', 'created_at', 'updated_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Reminder model"


# ==============================================================================
# FOREIGN KEY TESTS (Tests 126-127)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_user_id_foreign_key():
    """
    Test #126: Verify user_id is a foreign key to users

    Each reminder belongs to a user.
    """
    # Arrange
    mapper = inspect(Reminder)
    user_id_col = mapper.columns['user_id']

    # Act & Assert
    assert len(user_id_col.foreign_keys) > 0

    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_vault_file_id_foreign_key():
    """
    Test #127: Verify vault_file_id is a foreign key to vault_files

    Reminder is linked to a specific vault file field.
    """
    # Arrange
    mapper = inspect(Reminder)
    vault_file_id_col = mapper.columns['vault_file_id']

    # Act & Assert
    assert len(vault_file_id_col.foreign_keys) > 0

    fk = list(vault_file_id_col.foreign_keys)[0]
    assert 'vault_files.file_id' in str(fk.target_fullname)


# ==============================================================================
# COLUMN TYPE TESTS (Test 128)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_reminder_date_column():
    """
    Test #128: Verify reminder_date column is Date type

    Reminder date stores when to notify the user.
    """
    # Arrange
    mapper = inspect(Reminder)
    reminder_date_col = mapper.columns['reminder_date']

    # Act & Assert
    assert 'Date' in str(type(reminder_date_col.type)) or 'DATE' in str(reminder_date_col.type)


# ==============================================================================
# COLUMN PRESENCE TESTS (Tests 129-130)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_status_column():
    """
    Test #129: Verify status column exists and has default

    Status tracks reminder state (pending, sent, dismissed).
    """
    # Arrange
    mapper = inspect(Reminder)
    status_col = mapper.columns['status']

    # Act & Assert
    assert status_col.default is not None or status_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_urgency_level_column():
    """
    Test #130: Verify urgency_level column exists

    Urgency level defines reminder priority.
    """
    # Arrange
    mapper = inspect(Reminder)
    urgency_col = mapper.columns['urgency_level']

    # Act & Assert
    assert urgency_col is not None


# ==============================================================================
# RELATIONSHIP TESTS (Tests 131-132)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_user_relationship():
    """
    Test #131: Verify reminder.user relationship exists

    Validates relationship to the user.
    """
    # Arrange
    mapper = inspect(Reminder)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'user' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_vault_file_relationship():
    """
    Test #132: Verify reminder.vault_file relationship exists

    Validates relationship to the vault file.
    """
    # Arrange
    mapper = inspect(Reminder)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'vault_file' in relationship_names


# ==============================================================================
# MODEL BEHAVIOR TESTS (Test 133)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_reminder_repr_method():
    """
    Test #133: Verify Reminder __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    from datetime import date
    reminder = Reminder(
        user_id=1,
        vault_file_id="test123",
        field_name="test_field",
        reminder_category="test",
        trigger_date=date.today(),
        reminder_date=date.today(),
        title="Test Reminder",
        message="Test message",
        urgency_level="medium"
    )

    # Act
    repr_str = repr(reminder)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0
