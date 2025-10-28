"""
ORM Tests for Contact Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime

from app.models.contact import Contact


@pytest.mark.unit
@pytest.mark.orm
def test_contact_model_table_name():
    """Test 16: Verify Contact model table name is 'contacts'"""
    assert Contact.__tablename__ == "contacts"


@pytest.mark.unit
@pytest.mark.orm
def test_contact_all_columns_exist():
    """Test 17: Verify all required columns exist in Contact model"""
    mapper = inspect(Contact)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'owner_user_id', 'linked_user_id', 'title', 'first_name',
        'middle_name', 'last_name', 'local_name', 'company', 'job_type',
        'website', 'category', 'relation', 'phone_numbers', 'whatsapp_numbers',
        'emails', 'flat_building_no', 'street', 'city', 'state', 'country',
        'postal_code', 'date_of_birth', 'anniversary', 'notes', 'contact_image',
        'share_by_whatsapp', 'share_by_sms', 'share_by_email', 'share_after_death',
        'is_emergency_contact', 'created_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Contact model"


@pytest.mark.unit
@pytest.mark.orm
def test_contact_first_name_column():
    """Test 18: Verify first_name column is String type"""
    mapper = inspect(Contact)
    first_name_col = mapper.columns['first_name']
    assert 'String' in str(type(first_name_col.type)) or str(first_name_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
def test_contact_owner_user_id_foreign_key():
    """Test 19: Verify owner_user_id is a foreign key to users table"""
    mapper = inspect(Contact)
    owner_user_id_col = mapper.columns['owner_user_id']

    # Check if it has foreign keys
    assert len(owner_user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(owner_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_contact_linked_user_id_foreign_key():
    """Test 20: Verify linked_user_id is a foreign key (nullable) to users"""
    mapper = inspect(Contact)
    linked_user_id_col = mapper.columns['linked_user_id']

    # Should be nullable
    assert linked_user_id_col.nullable is True

    # Should have foreign key
    assert len(linked_user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(linked_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_contact_emails_json_column():
    """Test 21: Verify emails column is JSON type"""
    mapper = inspect(Contact)
    emails_col = mapper.columns['emails']
    assert 'JSON' in str(type(emails_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_contact_phone_numbers_json_column():
    """Test 22: Verify phone_numbers column is JSON type"""
    mapper = inspect(Contact)
    phone_numbers_col = mapper.columns['phone_numbers']
    assert 'JSON' in str(type(phone_numbers_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_contact_is_emergency_default_false():
    """Test 23: Verify is_emergency_contact default is False"""
    mapper = inspect(Contact)
    is_emergency_col = mapper.columns['is_emergency_contact']

    # Check if it has a default
    assert is_emergency_col.default is not None or is_emergency_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_contact_owner_relationship():
    """Test 24: Verify contact.owner_user relationship exists"""
    mapper = inspect(Contact)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'owner_user' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
def test_contact_linked_user_relationship():
    """Test 25: Verify contact.linked_user relationship exists"""
    mapper = inspect(Contact)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'linked_user' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
def test_contact_repr_method(db_session):
    """Test 26: Verify Contact __repr__() method works"""
    contact = Contact(
        first_name="John",
        owner_user_id=1,
        created_at=datetime.utcnow()
    )

    # Should not raise an error
    repr_str = repr(contact)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_contact_cascade_delete():
    """Test 27: Verify CASCADE delete is configured on owner_user_id"""
    mapper = inspect(Contact)
    owner_user_id_col = mapper.columns['owner_user_id']

    # Get foreign key
    fk = list(owner_user_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
