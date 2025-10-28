"""
ORM Tests for Reminder Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.reminder import Reminder


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_table_name():
    """Test 124: Verify Reminder model table name is 'reminders'"""
    assert Reminder.__tablename__ == "reminders"


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_all_columns_exist():
    """Test 125: Verify all required columns exist in Reminder model"""
    mapper = inspect(Reminder)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'user_id', 'vault_file_id', 'field_name', 'reminder_category',
        'trigger_date', 'reminder_date', 'title', 'message', 'urgency_level',
        'status', 'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Reminder model"


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_user_id_foreign_key():
    """Test 126: Verify user_id is a foreign key to users"""
    mapper = inspect(Reminder)
    user_id_col = mapper.columns['user_id']

    # Check if it has foreign keys
    assert len(user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_vault_file_id_foreign_key():
    """Test 127: Verify vault_file_id is a foreign key to vault_files"""
    mapper = inspect(Reminder)
    vault_file_id_col = mapper.columns['vault_file_id']

    # Check if it has foreign keys
    assert len(vault_file_id_col.foreign_keys) > 0

    # Check that it references vault_files.file_id
    fk = list(vault_file_id_col.foreign_keys)[0]
    assert 'vault_files.file_id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_reminder_date_column():
    """Test 128: Verify reminder_date column is Date type"""
    mapper = inspect(Reminder)
    reminder_date_col = mapper.columns['reminder_date']
    assert 'Date' in str(type(reminder_date_col.type)) or 'DATE' in str(reminder_date_col.type)


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_status_column():
    """Test 129: Verify status column exists and has default"""
    mapper = inspect(Reminder)
    status_col = mapper.columns['status']

    # Should have a default value
    assert status_col.default is not None or status_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_urgency_level_column():
    """Test 130: Verify urgency_level column exists"""
    mapper = inspect(Reminder)
    urgency_col = mapper.columns['urgency_level']
    assert urgency_col is not None


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_user_relationship():
    """Test 131: Verify reminder.user relationship exists"""
    mapper = inspect(Reminder)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'user' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_vault_file_relationship():
    """Test 132: Verify reminder.vault_file relationship exists"""
    mapper = inspect(Reminder)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'vault_file' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
def test_reminder_repr_method():
    """Test 133: Verify Reminder __repr__() method works"""
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

    # Should not raise an error
    repr_str = repr(reminder)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0
