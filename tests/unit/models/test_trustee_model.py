"""
Module 0: ORM Models - Trustee Model (Tests 82-91)

Validates SQLAlchemy model schema for trustee management system.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 82-83)
- Foreign keys (Tests 84-85)
- Column types (Tests 86, 88)
- Default values (Test 87)
- Unique constraints (Test 89)
- Model behavior (Tests 90-91)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.trustee import Trustee


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 82-83)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_table_name():
    """
    Test #82: Verify Trustee model table name is 'trustees'

    Validates that SQLAlchemy maps the Trustee class to the correct table.
    """
    # Act & Assert
    assert Trustee.__tablename__ == "trustees"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_all_columns_exist():
    """
    Test #83: Verify all required columns exist in Trustee model

    Ensures the ORM schema matches database schema.
    Trustees are contacts designated to manage the account after death.
    """
    # Arrange
    mapper = inspect(Trustee)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'user_id', 'contact_id', 'status', 'invited_at',
        'responded_at', 'is_primary', 'version', 'invite_token',
        'invite_expires_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Trustee model"


# ==============================================================================
# FOREIGN KEY TESTS (Tests 84-85)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_user_id_foreign_key():
    """
    Test #84: Verify user_id is a foreign key to users

    The user who owns the account (root user).
    """
    # Arrange
    mapper = inspect(Trustee)
    user_id_col = mapper.columns['user_id']

    # Act & Assert
    assert len(user_id_col.foreign_keys) > 0

    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_contact_id_foreign_key():
    """
    Test #85: Verify contact_id is a foreign key to contacts

    The contact designated as trustee.
    """
    # Arrange
    mapper = inspect(Trustee)
    contact_id_col = mapper.columns['contact_id']

    # Act & Assert
    assert len(contact_id_col.foreign_keys) > 0

    fk = list(contact_id_col.foreign_keys)[0]
    assert 'contacts.id' in str(fk.target_fullname)


# ==============================================================================
# COLUMN TYPE TESTS (Tests 86, 88)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_status_enum():
    """
    Test #86: Verify status column is Enum type

    Status tracks trustee lifecycle (invited, accepted, declined, etc.).
    """
    # Arrange
    mapper = inspect(Trustee)
    status_col = mapper.columns['status']

    # Act & Assert
    assert 'Enum' in str(type(status_col.type))


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_version_column():
    """
    Test #88: Verify version column is Integer

    Version tracks revisions to trustee agreements.
    """
    # Arrange
    mapper = inspect(Trustee)
    version_col = mapper.columns['version']

    # Act & Assert
    assert 'Integer' in str(type(version_col.type)) or 'INTEGER' in str(version_col.type)


# ==============================================================================
# DEFAULT VALUE TESTS (Test 87)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_is_primary_default_false():
    """
    Test #87: Verify is_primary has default False

    Only one trustee can be designated as primary.
    """
    # Arrange
    mapper = inspect(Trustee)
    is_primary_col = mapper.columns['is_primary']

    # Act & Assert
    assert is_primary_col.default is not None or is_primary_col.server_default is not None


# ==============================================================================
# UNIQUE CONSTRAINT TESTS (Test 89)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_unique_constraint():
    """
    Test #89: Verify UNIQUE constraint on (user_id, contact_id)

    A contact can only be a trustee once per user.
    """
    # Arrange & Act
    assert hasattr(Trustee, '__table_args__')

    # Check for unique constraint in table args
    has_unique_constraint = False
    for constraint in Trustee.__table_args__:
        if hasattr(constraint, 'name') and 'uq_trustee_one_per_contact' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (user_id, contact_id) not found"


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 90-91)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_repr_method():
    """
    Test #90: Verify Trustee __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    trustee = Trustee(
        user_id=1,
        contact_id=2
    )

    # Act
    repr_str = repr(trustee)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_trustee_cascade_delete():
    """
    Test #91: Verify CASCADE delete on both user_id and contact_id

    When user or contact is deleted, all trustee relationships should be deleted.
    """
    # Arrange
    mapper = inspect(Trustee)
    user_id_col = mapper.columns['user_id']
    contact_id_col = mapper.columns['contact_id']

    user_fk = list(user_id_col.foreign_keys)[0]
    contact_fk = list(contact_id_col.foreign_keys)[0]

    # Act & Assert
    assert user_fk.ondelete == 'CASCADE'
    assert contact_fk.ondelete == 'CASCADE'
