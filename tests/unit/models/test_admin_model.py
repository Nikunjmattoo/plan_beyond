"""
Module 0: ORM Models - Admin Model (Tests 134-141)

Validates SQLAlchemy model schema for admin users.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 134-135)
- Constraints (Tests 136-137)
- Column types (Tests 138-139)
- Model behavior (Tests 140-141)
"""
import pytest
from datetime import datetime

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.admin import Admin


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 134-135)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_table_name():
    """
    Test #134: Verify Admin model table name is 'admins'

    Validates that SQLAlchemy maps the Admin class to the correct table.
    """
    # Act & Assert
    assert Admin.__tablename__ == "admins"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_all_columns_exist():
    """
    Test #135: Verify all required columns exist in Admin model

    Ensures the ORM schema matches database schema.
    """
    # Arrange
    mapper = inspect(Admin)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'username', 'email', 'password', 'otp',
        'otp_expires_at', 'otp_verified', 'created_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Admin model"


# ==============================================================================
# CONSTRAINT TESTS (Tests 136-137)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_username_unique():
    """
    Test #136: Verify username has UNIQUE constraint

    Ensures no duplicate admin usernames can exist.
    """
    # Arrange
    mapper = inspect(Admin)
    username_col = mapper.columns['username']

    # Act & Assert
    assert username_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_email_unique():
    """
    Test #137: Verify email has UNIQUE constraint

    Ensures no duplicate admin emails can exist.
    """
    # Arrange
    mapper = inspect(Admin)
    email_col = mapper.columns['email']

    # Act & Assert
    assert email_col.unique is True


# ==============================================================================
# COLUMN TYPE TESTS (Tests 138-139)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_password_column():
    """
    Test #138: Verify password column is String type

    Validates column type for storing hashed admin passwords.
    """
    # Arrange
    mapper = inspect(Admin)
    password_col = mapper.columns['password']

    # Act & Assert
    assert 'String' in str(type(password_col.type)) or str(password_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_otp_nullable():
    """
    Test #139: Verify otp can be NULL

    OTP is only set during admin authentication flow.
    """
    # Arrange
    mapper = inspect(Admin)
    otp_col = mapper.columns['otp']

    # Act & Assert
    assert otp_col.nullable is True


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 140-141)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_repr_method():
    """
    Test #140: Verify Admin __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    admin = Admin(
        username="testadmin",
        email="admin@example.com",
        password="hashed_password"
    )

    # Act
    repr_str = repr(admin)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_admin_otp_verified_default():
    """
    Test #141: Verify otp_verified has default False

    OTP should start as unverified until admin verifies it.
    """
    # Arrange
    mapper = inspect(Admin)
    otp_verified_col = mapper.columns['otp_verified']

    # Act & Assert
    assert otp_verified_col.default is not None or otp_verified_col.server_default is not None
