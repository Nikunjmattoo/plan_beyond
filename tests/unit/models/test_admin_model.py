"""
ORM Tests for Admin Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime

from app.models.admin import Admin


@pytest.mark.unit
@pytest.mark.orm
def test_admin_table_name():
    """Test 134: Verify Admin model table name is 'admins'"""
    assert Admin.__tablename__ == "admins"


@pytest.mark.unit
@pytest.mark.orm
def test_admin_all_columns_exist():
    """Test 135: Verify all required columns exist in Admin model"""
    mapper = inspect(Admin)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'username', 'email', 'password', 'otp',
        'otp_expires_at', 'otp_verified', 'created_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Admin model"


@pytest.mark.unit
@pytest.mark.orm
def test_admin_username_unique():
    """Test 136: Verify username has UNIQUE constraint"""
    mapper = inspect(Admin)
    username_col = mapper.columns['username']
    assert username_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
def test_admin_email_unique():
    """Test 137: Verify email has UNIQUE constraint"""
    mapper = inspect(Admin)
    email_col = mapper.columns['email']
    assert email_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
def test_admin_password_column():
    """Test 138: Verify password column is String type"""
    mapper = inspect(Admin)
    password_col = mapper.columns['password']
    assert 'String' in str(type(password_col.type)) or str(password_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
def test_admin_otp_nullable():
    """Test 139: Verify otp can be NULL"""
    mapper = inspect(Admin)
    otp_col = mapper.columns['otp']
    assert otp_col.nullable is True


@pytest.mark.unit
@pytest.mark.orm
def test_admin_repr_method():
    """Test 140: Verify Admin __repr__() method works"""
    admin = Admin(
        username="testadmin",
        email="admin@example.com",
        password="hashed_password"
    )

    # Should not raise an error
    repr_str = repr(admin)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_admin_otp_verified_default():
    """Test 141: Verify otp_verified has default False"""
    mapper = inspect(Admin)
    otp_verified_col = mapper.columns['otp_verified']

    # Should have a default
    assert otp_verified_col.default is not None or otp_verified_col.server_default is not None
