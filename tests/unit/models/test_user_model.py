"""
ORM Tests for User Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty
from datetime import datetime

from app.models.user import User, UserProfile, UserStatus


@pytest.mark.unit
@pytest.mark.orm
def test_user_model_table_name():
    """Test 1: Verify User model table name is 'users'"""
    assert User.__tablename__ == "users"


@pytest.mark.unit
@pytest.mark.orm
def test_user_model_all_columns_exist():
    """Test 2: Verify all required columns exist in User model"""
    mapper = inspect(User)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'display_name', 'email', 'country_code', 'phone',
        'password', 'status', 'communication_channel', 'otp',
        'otp_expires_at', 'otp_verified', 'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in User model"


@pytest.mark.unit
@pytest.mark.orm
def test_user_email_column_type():
    """Test 3: Verify email column is String type"""
    mapper = inspect(User)
    email_col = mapper.columns['email']
    assert str(email_col.type) == 'VARCHAR' or 'String' in str(type(email_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_user_phone_column_type():
    """Test 4: Verify phone column is String type"""
    mapper = inspect(User)
    phone_col = mapper.columns['phone']
    assert str(phone_col.type) == 'VARCHAR' or 'String' in str(type(phone_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_user_password_column_type():
    """Test 5: Verify password column is String type"""
    mapper = inspect(User)
    password_col = mapper.columns['password']
    assert str(password_col.type) == 'VARCHAR' or 'String' in str(type(password_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_user_status_column_enum():
    """Test 6: Verify status column is UserStatus enum"""
    mapper = inspect(User)
    status_col = mapper.columns['status']
    # Check if it's an Enum type
    assert 'Enum' in str(type(status_col.type)) or hasattr(status_col.type, 'enum_class')


@pytest.mark.unit
@pytest.mark.orm
def test_user_email_unique_constraint():
    """Test 7: Verify email has UNIQUE constraint"""
    mapper = inspect(User)
    email_col = mapper.columns['email']
    assert email_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
def test_user_phone_unique_constraint():
    """Test 8: Verify phone has UNIQUE constraint"""
    mapper = inspect(User)
    phone_col = mapper.columns['phone']
    assert phone_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
def test_user_email_nullable():
    """Test 9: Verify email nullable is True (can be NULL)"""
    mapper = inspect(User)
    email_col = mapper.columns['email']
    assert email_col.nullable is True


@pytest.mark.unit
@pytest.mark.orm
def test_user_otp_nullable_true():
    """Test 10: Verify otp can be NULL"""
    mapper = inspect(User)
    otp_col = mapper.columns['otp']
    assert otp_col.nullable is True


@pytest.mark.unit
@pytest.mark.orm
def test_user_relationships_defined():
    """Test 11: Verify all relationships are defined on User model"""
    mapper = inspect(User)
    relationship_names = [rel.key for rel in mapper.relationships]

    expected_relationships = [
        'profile', 'contacts', 'files', 'verifications',
        'status_history', 'reminders', 'reminder_preference'
    ]

    for rel in expected_relationships:
        assert rel in relationship_names, f"Relationship '{rel}' not found in User model"


@pytest.mark.unit
@pytest.mark.orm
def test_user_profile_relationship():
    """Test 12: Verify user.profile relationship configuration"""
    mapper = inspect(User)
    profile_rel = mapper.relationships['profile']

    # Should be one-to-one (uselist=False)
    assert profile_rel.uselist is False
    # Should cascade delete
    assert 'delete-orphan' in str(profile_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_user_contacts_relationship():
    """Test 13: Verify user.contacts relationship configuration"""
    mapper = inspect(User)
    contacts_rel = mapper.relationships['contacts']

    # Should be one-to-many (uselist=True)
    assert contacts_rel.uselist is True
    # Should cascade delete
    assert 'delete-orphan' in str(contacts_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_user_repr_method(db_session):
    """Test 14: Verify User __repr__() method exists and works"""
    user = User(
        email="test@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Should not raise an error
    repr_str = repr(user)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_user_status_enum_values():
    """Test 15: Verify UserStatus enum has correct values"""
    assert hasattr(UserStatus, 'unknown')
    assert hasattr(UserStatus, 'guest')
    assert hasattr(UserStatus, 'verified')
    assert hasattr(UserStatus, 'member')

    assert UserStatus.unknown.value == 'unknown'
    assert UserStatus.guest.value == 'guest'
    assert UserStatus.verified.value == 'verified'
    assert UserStatus.member.value == 'member'
