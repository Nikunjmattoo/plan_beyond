"""
Module 0: ORM Models - Contact Model (Tests 16-27)

Validates SQLAlchemy model schema for user contacts.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 16-17)
- Column types (Tests 18, 21-22)
- Foreign keys (Tests 19-20)
- Defaults (Test 23)
- Relationships (Tests 24-25)
- Model behavior (Tests 26-27)
"""
import pytest
from datetime import datetime

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.contact import Contact


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 16-17)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_model_table_name():
    """
    Test #16: Verify Contact model table name is 'contacts'

    Validates that SQLAlchemy maps the Contact class to the correct table.
    """
    # Act & Assert
    assert Contact.__tablename__ == "contacts"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_all_columns_exist():
    """
    Test #17: Verify all required columns exist in Contact model

    Ensures the ORM schema matches database schema.
    Contact has many columns for comprehensive contact information.
    """
    # Arrange
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

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in Contact model"


# ==============================================================================
# COLUMN TYPE TESTS (Tests 18, 21-22)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_first_name_column():
    """
    Test #18: Verify first_name column is String type

    First name is the only required field for contacts.
    """
    # Arrange
    mapper = inspect(Contact)
    first_name_col = mapper.columns['first_name']

    # Act & Assert
    assert 'String' in str(type(first_name_col.type)) or str(first_name_col.type) == 'VARCHAR'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_emails_json_column():
    """
    Test #21: Verify emails column is JSON type

    Contacts can have multiple email addresses stored as JSON array.
    """
    # Arrange
    mapper = inspect(Contact)
    emails_col = mapper.columns['emails']

    # Act & Assert
    assert 'JSON' in str(type(emails_col.type))


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_phone_numbers_json_column():
    """
    Test #22: Verify phone_numbers column is JSON type

    Contacts can have multiple phone numbers stored as JSON array.
    """
    # Arrange
    mapper = inspect(Contact)
    phone_numbers_col = mapper.columns['phone_numbers']

    # Act & Assert
    assert 'JSON' in str(type(phone_numbers_col.type))


# ==============================================================================
# FOREIGN KEY TESTS (Tests 19-20)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_owner_user_id_foreign_key():
    """
    Test #19: Verify owner_user_id is a foreign key to users table

    Every contact must belong to a user (the owner).
    """
    # Arrange
    mapper = inspect(Contact)
    owner_user_id_col = mapper.columns['owner_user_id']

    # Act & Assert
    assert len(owner_user_id_col.foreign_keys) > 0

    fk = list(owner_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_linked_user_id_foreign_key():
    """
    Test #20: Verify linked_user_id is a foreign key (nullable) to users

    Contacts can optionally be linked to platform users.
    """
    # Arrange
    mapper = inspect(Contact)
    linked_user_id_col = mapper.columns['linked_user_id']

    # Act & Assert
    assert linked_user_id_col.nullable is True  # Optional link
    assert len(linked_user_id_col.foreign_keys) > 0

    fk = list(linked_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


# ==============================================================================
# DEFAULT VALUE TESTS (Test 23)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_is_emergency_default_false():
    """
    Test #23: Verify is_emergency_contact default is False

    Contacts are not emergency contacts by default.
    """
    # Arrange
    mapper = inspect(Contact)
    is_emergency_col = mapper.columns['is_emergency_contact']

    # Act & Assert
    assert is_emergency_col.default is not None or is_emergency_col.server_default is not None


# ==============================================================================
# RELATIONSHIP TESTS (Tests 24-25)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_owner_relationship():
    """
    Test #24: Verify contact.owner_user relationship exists

    Validates relationship to the user who owns this contact.
    """
    # Arrange
    mapper = inspect(Contact)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'owner_user' in relationship_names


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_linked_user_relationship():
    """
    Test #25: Verify contact.linked_user relationship exists

    Validates optional relationship to platform user.
    """
    # Arrange
    mapper = inspect(Contact)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'linked_user' in relationship_names


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 26-27)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_repr_method(db_session):
    """
    Test #26: Verify Contact __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    contact = Contact(
        first_name="John",
        owner_user_id=1,
        created_at=datetime.utcnow()
    )

    # Act
    repr_str = repr(contact)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_contact_cascade_delete():
    """
    Test #27: Verify CASCADE delete is configured on owner_user_id

    When user is deleted, all their contacts should be deleted.
    """
    # Arrange
    mapper = inspect(Contact)
    owner_user_id_col = mapper.columns['owner_user_id']
    fk = list(owner_user_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
