"""
Module 0: ORM Models - User Model (Tests 1-15)

Validates SQLAlchemy model schema, relationships, and constraints.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 1-2)
- Column types (Tests 3-6)
- Constraints (Tests 7-10)
- Relationships (Tests 11-13)
- Model behavior (Tests 14-15)
"""
import pytest
from datetime import datetime

# Third-party
from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty

# Application imports
from app.models.user import User, UserProfile, UserStatus


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 1-2)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_model_table_name():
    """
    Test #1: Verify User model table name is 'users'

    Validates that SQLAlchemy maps the User class to the correct table.
    Mismatch would cause all user queries to fail.
    """
    # Act & Assert
    assert User.__tablename__ == "users"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_model_all_columns_exist():
    """
    Test #2: Verify all required columns exist in User model

    Ensures the ORM schema matches database schema.
    Missing columns would cause runtime errors.
    """
    # Arrange
    mapper = inspect(User)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'display_name', 'email', 'country_code', 'phone',
        'password', 'status', 'communication_channel', 'otp',
        'otp_expires_at', 'otp_verified', 'created_at', 'updated_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in User model"


# ==============================================================================
# COLUMN TYPE TESTS (Tests 3-6)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_email_column_type():
    """
    Test #3: Verify email column is String type

    Validates the column type to ensure proper data storage.
    """
    # Arrange
    mapper = inspect(User)
    email_col = mapper.columns['email']

    # Act & Assert
    assert str(email_col.type) == 'VARCHAR' or 'String' in str(type(email_col.type))


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_phone_column_type():
    """
    Test #4: Verify phone column is String type

    Validates the column type to ensure proper data storage.
    """
    # Arrange
    mapper = inspect(User)
    phone_col = mapper.columns['phone']

    # Act & Assert
    assert str(phone_col.type) == 'VARCHAR' or 'String' in str(type(phone_col.type))


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_password_column_type():
    """
    Test #5: Verify password column is String type

    Validates the column type for storing hashed passwords.
    """
    # Arrange
    mapper = inspect(User)
    password_col = mapper.columns['password']

    # Act & Assert
    assert str(password_col.type) == 'VARCHAR' or 'String' in str(type(password_col.type))


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_status_column_enum():
    """
    Test #6: Verify status column is UserStatus enum

    Validates that status uses proper enum type for data integrity.
    """
    # Arrange
    mapper = inspect(User)
    status_col = mapper.columns['status']

    # Act & Assert
    assert 'Enum' in str(type(status_col.type)) or hasattr(status_col.type, 'enum_class')


# ==============================================================================
# CONSTRAINT TESTS (Tests 7-10)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_email_unique_constraint():
    """
    Test #7: Verify email has UNIQUE constraint

    Ensures no duplicate emails can exist in database.
    """
    # Arrange
    mapper = inspect(User)
    email_col = mapper.columns['email']

    # Act & Assert
    assert email_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_phone_unique_constraint():
    """
    Test #8: Verify phone has UNIQUE constraint

    Ensures no duplicate phone numbers can exist in database.
    """
    # Arrange
    mapper = inspect(User)
    phone_col = mapper.columns['phone']

    # Act & Assert
    assert phone_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_email_nullable():
    """
    Test #9: Verify email nullable is True (can be NULL)

    Users can register with phone only, so email is optional.
    """
    # Arrange
    mapper = inspect(User)
    email_col = mapper.columns['email']

    # Act & Assert
    assert email_col.nullable is True


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_otp_nullable_true():
    """
    Test #10: Verify otp can be NULL

    OTP is only set during authentication flow, not always present.
    """
    # Arrange
    mapper = inspect(User)
    otp_col = mapper.columns['otp']

    # Act & Assert
    assert otp_col.nullable is True


# ==============================================================================
# RELATIONSHIP TESTS (Tests 11-13)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_relationships_defined():
    """
    Test #11: Verify all relationships are defined on User model

    Validates that all foreign key relationships are properly configured.
    Missing relationships would break queries and cause errors.
    """
    # Arrange
    mapper = inspect(User)
    relationship_names = [rel.key for rel in mapper.relationships]

    expected_relationships = [
        'profile', 'contacts', 'files', 'verifications',
        'status_history', 'reminders', 'reminder_preference'
    ]

    # Act & Assert
    for rel in expected_relationships:
        assert rel in relationship_names, f"Relationship '{rel}' not found in User model"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_profile_relationship():
    """
    Test #12: Verify user.profile relationship configuration

    Validates 1:1 relationship with cascade delete.
    User deletion should delete their profile.
    """
    # Arrange
    mapper = inspect(User)
    profile_rel = mapper.relationships['profile']

    # Act & Assert
    assert profile_rel.uselist is False  # One-to-one
    assert 'delete-orphan' in str(profile_rel.cascade)  # Cascade delete


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_contacts_relationship():
    """
    Test #13: Verify user.contacts relationship configuration

    Validates 1:N relationship with cascade delete.
    User deletion should delete all their contacts.
    """
    # Arrange
    mapper = inspect(User)
    contacts_rel = mapper.relationships['contacts']

    # Act & Assert
    assert contacts_rel.uselist is True  # One-to-many
    assert 'delete-orphan' in str(contacts_rel.cascade)  # Cascade delete


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 14-15)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_repr_method(db_session):
    """
    Test #14: Verify User __repr__() method exists and works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    user = User(
        email="test@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Act
    repr_str = repr(user)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_status_enum_values():
    """
    Test #15: Verify UserStatus enum has correct values

    Validates the user lifecycle status enum values.
    These must match database enum definition.
    """
    # Act & Assert
    assert hasattr(UserStatus, 'unknown')
    assert hasattr(UserStatus, 'guest')
    assert hasattr(UserStatus, 'verified')
    assert hasattr(UserStatus, 'member')

    assert UserStatus.unknown.value == 'unknown'
    assert UserStatus.guest.value == 'guest'
    assert UserStatus.verified.value == 'verified'
    assert UserStatus.member.value == 'member'
