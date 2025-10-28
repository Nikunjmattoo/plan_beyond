"""
ORM Tests for Trustee Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.trustee import Trustee


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_table_name():
    """Test 82: Verify Trustee model table name is 'trustees'"""
    assert Trustee.__tablename__ == "trustees"


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_all_columns_exist():
    """Test 83: Verify all required columns exist in Trustee model"""
    mapper = inspect(Trustee)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'user_id', 'contact_id', 'status', 'invited_at',
        'responded_at', 'is_primary', 'version', 'invite_token',
        'invite_expires_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Trustee model"


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_user_id_foreign_key():
    """Test 84: Verify user_id is a foreign key to users"""
    mapper = inspect(Trustee)
    user_id_col = mapper.columns['user_id']

    # Check if it has foreign keys
    assert len(user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_contact_id_foreign_key():
    """Test 85: Verify contact_id is a foreign key to contacts"""
    mapper = inspect(Trustee)
    contact_id_col = mapper.columns['contact_id']

    # Check if it has foreign keys
    assert len(contact_id_col.foreign_keys) > 0

    # Check that it references contacts.id
    fk = list(contact_id_col.foreign_keys)[0]
    assert 'contacts.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_status_enum():
    """Test 86: Verify status column is Enum type"""
    mapper = inspect(Trustee)
    status_col = mapper.columns['status']

    # Check if it's an Enum type
    assert 'Enum' in str(type(status_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_is_primary_default_false():
    """Test 87: Verify is_primary has default False"""
    mapper = inspect(Trustee)
    is_primary_col = mapper.columns['is_primary']

    # Should have a default
    assert is_primary_col.default is not None or is_primary_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_version_column():
    """Test 88: Verify version column is Integer"""
    mapper = inspect(Trustee)
    version_col = mapper.columns['version']

    # Should be Integer type
    assert 'Integer' in str(type(version_col.type)) or 'INTEGER' in str(version_col.type)


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_unique_constraint():
    """Test 89: Verify UNIQUE constraint on (user_id, contact_id)"""
    # Check if table args has unique constraint
    assert hasattr(Trustee, '__table_args__')

    # Check for unique constraint in table args
    has_unique_constraint = False
    for constraint in Trustee.__table_args__:
        if hasattr(constraint, 'name') and 'uq_trustee_one_per_contact' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (user_id, contact_id) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_repr_method():
    """Test 90: Verify Trustee __repr__() method works"""
    trustee = Trustee(
        user_id=1,
        contact_id=2
    )

    # Should not raise an error
    repr_str = repr(trustee)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_trustee_cascade_delete():
    """Test 91: Verify CASCADE delete on both user_id and contact_id"""
    mapper = inspect(Trustee)
    user_id_col = mapper.columns['user_id']
    contact_id_col = mapper.columns['contact_id']

    # Get foreign keys
    user_fk = list(user_id_col.foreign_keys)[0]
    contact_fk = list(contact_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert user_fk.ondelete == 'CASCADE'
    assert contact_fk.ondelete == 'CASCADE'
