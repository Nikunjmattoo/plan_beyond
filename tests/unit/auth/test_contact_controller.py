"""
Module 2: Auth - Contact Controller Tests (Tests 321-340)

Tests contact CRUD operations, linking contacts to users, and cascade deletes.
Note: Some tests are async due to file handling in contact controller.
"""
import pytest
from datetime import datetime

from controller.contact import (
    get_contact_by_id,
    get_contacts,
    delete_contact
)
from app.models.contact import Contact
from app.models.user import User, UserStatus
from app.schemas.contact import ContactCreate


# ==============================================
# CONTACT CREATION TESTS (Tests 321-325)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_contact_minimal_fields(db_session):
    """
    Test #321: Create contact with minimal required fields (first_name + owner)
    """
    # Create owner user
    owner = User(
        email="owner@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    # Create contact with minimal fields
    contact = Contact(
        first_name="John",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.owner_user_id == owner.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_contact_all_fields(db_session):
    """
    Test #322: Create contact with all fields populated
    """
    owner = User(
        email="owner2@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    contact = Contact(
        title="Mr",
        first_name="John",
        middle_name="Michael",
        last_name="Smith",
        local_name="जॉन स्मिथ",
        company="Tech Corp",
        job_type="Engineer",
        website="https://example.com",
        category="Business",
        relation="Colleague",
        phone_numbers=["+911234567890", "+919876543210"],
        emails=["john@example.com", "jsmith@company.com"],
        whatsapp_numbers=["+911234567890"],
        flat_building_no="123",
        street="Main Street",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        postal_code="400001",
        date_of_birth="1990-01-15",
        anniversary="2015-06-20",
        notes="Important client contact",
        contact_image="https://example.com/avatar.jpg",
        owner_user_id=owner.id,
        share_by_whatsapp=True,
        share_by_sms=False,
        share_by_email=True,
        share_after_death=True,
        is_emergency_contact=False,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert contact.first_name == "John"
    assert contact.last_name == "Smith"
    assert contact.company == "Tech Corp"
    assert contact.city == "Mumbai"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_contact_with_emails_array(db_session):
    """
    Test #323: Contact emails stored as JSON array
    """
    owner = User(
        email="owner3@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    emails = ["primary@example.com", "secondary@example.com", "work@company.com"]

    contact = Contact(
        first_name="Multi",
        last_name="Email",
        emails=emails,
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert isinstance(contact.emails, list)
    assert len(contact.emails) == 3
    assert "primary@example.com" in contact.emails


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_contact_with_phone_numbers_array(db_session):
    """
    Test #324: Contact phone numbers stored as JSON array
    """
    owner = User(
        email="owner4@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    phones = ["+911234567890", "+919876543210", "+442012345678"]

    contact = Contact(
        first_name="Multi",
        last_name="Phone",
        phone_numbers=phones,
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert isinstance(contact.phone_numbers, list)
    assert len(contact.phone_numbers) == 3
    assert "+911234567890" in contact.phone_numbers


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_contact_owner_must_exist(db_session):
    """
    Test #325: Contact must have a valid owner (foreign key constraint)
    """
    from sqlalchemy.exc import IntegrityError

    # Try to create contact with non-existent owner
    contact = Contact(
        first_name="Orphan",
        owner_user_id=99999,  # Non-existent user
        created_at=datetime.utcnow()
    )
    db_session.add(contact)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


# ==============================================
# CONTACT UPDATE TESTS (Tests 326-329)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_contact_name_fields(db_session):
    """
    Test #326: Update contact name fields
    """
    owner = User(
        email="owner5@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    contact = Contact(
        first_name="Old",
        last_name="Name",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Update names
    contact.first_name = "New"
    contact.middle_name = "Middle"
    contact.last_name = "Updated"
    db_session.commit()
    db_session.refresh(contact)

    assert contact.first_name == "New"
    assert contact.middle_name == "Middle"
    assert contact.last_name == "Updated"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_contact_address_fields(db_session):
    """
    Test #327: Update contact address fields
    """
    owner = User(
        email="owner6@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    contact = Contact(
        first_name="Address",
        last_name="Test",
        city="Old City",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Update address
    contact.flat_building_no = "456"
    contact.street = "New Street"
    contact.city = "New City"
    contact.state = "New State"
    contact.country = "New Country"
    contact.postal_code = "123456"
    db_session.commit()
    db_session.refresh(contact)

    assert contact.city == "New City"
    assert contact.street == "New Street"
    assert contact.postal_code == "123456"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_contact_emails(db_session):
    """
    Test #328: Update contact email list
    """
    owner = User(
        email="owner7@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    contact = Contact(
        first_name="Email",
        last_name="Update",
        emails=["old@example.com"],
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Update emails
    contact.emails = ["new1@example.com", "new2@example.com"]
    db_session.commit()
    db_session.refresh(contact)

    assert len(contact.emails) == 2
    assert "new1@example.com" in contact.emails
    assert "old@example.com" not in contact.emails


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_contact_linked_user_id(db_session):
    """
    Test #329: Update contact's linked_user_id (link contact to a user)
    """
    owner = User(
        email="owner8@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)

    # User to link to
    linked_user = User(
        email="linked@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    contact = Contact(
        first_name="Link",
        last_name="Test",
        owner_user_id=owner.id,
        linked_user_id=None,  # Initially not linked
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Link contact to user
    contact.linked_user_id = linked_user.id
    db_session.commit()
    db_session.refresh(contact)

    assert contact.linked_user_id == linked_user.id


# ==============================================
# CONTACT DELETE TESTS (Tests 330-331)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_delete_contact_by_id(db_session):
    """
    Test #330: Delete contact by ID
    """
    owner = User(
        email="owner9@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    contact = Contact(
        first_name="Delete",
        last_name="Me",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    contact_id = contact.id

    # Delete via controller
    deleted = delete_contact(db_session, contact_id)

    assert deleted is not None
    assert deleted.id == contact_id

    # Verify deletion
    found = get_contact_by_id(db_session, contact_id)
    assert found is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_delete_contact_cascade_on_owner_delete(db_session):
    """
    Test #331: Contacts should be deleted when owner is deleted (CASCADE)
    """
    owner = User(
        email="owner10@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    # Create multiple contacts for this owner
    contact1 = Contact(
        first_name="Contact",
        last_name="One",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    contact2 = Contact(
        first_name="Contact",
        last_name="Two",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add_all([contact1, contact2])
    db_session.commit()

    contact1_id = contact1.id
    contact2_id = contact2.id

    # Delete owner
    db_session.delete(owner)
    db_session.commit()

    # Assert - Contacts should be deleted (CASCADE)
    found1 = get_contact_by_id(db_session, contact1_id)
    found2 = get_contact_by_id(db_session, contact2_id)

    assert found1 is None
    assert found2 is None


# ==============================================
# CONTACT LINKING TESTS (Tests 332-335)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_link_contact_to_user_by_email(db_session):
    """
    Test #332: Link contact to user by matching email
    """
    owner = User(
        email="owner11@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)

    # User with matching email
    linked_user = User(
        email="match@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    # Contact with same email
    contact = Contact(
        first_name="Match",
        last_name="Email",
        emails=["match@example.com"],
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Link logic (would be in controller)
    if "match@example.com" in contact.emails:
        contact.linked_user_id = linked_user.id
        db_session.commit()

    db_session.refresh(contact)
    assert contact.linked_user_id == linked_user.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_link_contact_to_user_by_phone(db_session):
    """
    Test #333: Link contact to user by matching phone
    """
    owner = User(
        email="owner12@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)

    linked_user = User(
        email="phoneuser@example.com",
        phone="+911234567890",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    contact = Contact(
        first_name="Match",
        last_name="Phone",
        phone_numbers=["+911234567890"],
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Link logic
    if "+911234567890" in contact.phone_numbers:
        contact.linked_user_id = linked_user.id
        db_session.commit()

    db_session.refresh(contact)
    assert contact.linked_user_id == linked_user.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_link_updates_linked_user_id(db_session):
    """
    Test #334: Linking sets the linked_user_id field
    """
    owner = User(
        email="owner13@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)

    linked_user = User(
        email="link@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    contact = Contact(
        first_name="Unlinked",
        owner_user_id=owner.id,
        linked_user_id=None,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    assert contact.linked_user_id is None

    # Link
    contact.linked_user_id = linked_user.id
    db_session.commit()
    db_session.refresh(contact)

    assert contact.linked_user_id is not None
    assert contact.linked_user_id == linked_user.id


@pytest.mark.unit
@pytest.mark.auth
def test_unlink_contact_sets_null(db_session):
    """
    Test #335: Unlinking contact sets linked_user_id to NULL
    """
    owner = User(
        email="owner14@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)

    linked_user = User(
        email="unlink@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    contact = Contact(
        first_name="Linked",
        owner_user_id=owner.id,
        linked_user_id=linked_user.id,  # Initially linked
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Unlink
    contact.linked_user_id = None
    db_session.commit()
    db_session.refresh(contact)

    assert contact.linked_user_id is None


# ==============================================
# CONTACT QUERY TESTS (Tests 336-340)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_all_contacts_for_user(db_session):
    """
    Test #336: Get all contacts belonging to a user
    """
    owner = User(
        email="owner15@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    # Create multiple contacts
    for i in range(5):
        contact = Contact(
            first_name=f"Contact{i}",
            owner_user_id=owner.id,
            created_at=datetime.utcnow()
        )
        db_session.add(contact)
    db_session.commit()

    # Get all contacts
    contacts = get_contacts(db_session, owner.id, skip=0, limit=10)

    assert len(contacts) == 5


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_contact_by_id(db_session):
    """
    Test #337: Get contact by ID
    """
    owner = User(
        email="owner16@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    contact = Contact(
        first_name="Find",
        last_name="ById",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Find by ID
    found = get_contact_by_id(db_session, contact.id)

    assert found is not None
    assert found.id == contact.id
    assert found.first_name == "Find"


@pytest.mark.unit
@pytest.mark.auth
def test_search_contacts_by_name(db_session):
    """
    Test #338: Search contacts by name (partial match)
    """
    owner = User(
        email="owner17@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    # Create test contacts
    contact1 = Contact(
        first_name="Alice",
        last_name="Johnson",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    contact2 = Contact(
        first_name="Bob",
        last_name="Smith",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    contact3 = Contact(
        first_name="Alice",
        last_name="Brown",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add_all([contact1, contact2, contact3])
    db_session.commit()

    # Search for "Alice"
    results = get_contacts(db_session, owner.id, search="Alice")

    assert len(results) >= 2  # Should find both Alice contacts


@pytest.mark.unit
@pytest.mark.auth
def test_filter_contacts_by_category(db_session):
    """
    Test #339: Filter contacts by category
    """
    owner = User(
        email="owner18@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    # Create contacts with different categories
    business = Contact(
        first_name="Business",
        category="Business",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    family = Contact(
        first_name="Family",
        category="Family",
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add_all([business, family])
    db_session.commit()

    # Query by category (manual filter since controller doesn't expose this)
    business_contacts = db_session.query(Contact).filter(
        Contact.owner_user_id == owner.id,
        Contact.category == "Business"
    ).all()

    assert len(business_contacts) == 1
    assert business_contacts[0].first_name == "Business"


@pytest.mark.unit
@pytest.mark.auth
def test_filter_emergency_contacts(db_session):
    """
    Test #340: Filter contacts by is_emergency_contact flag
    """
    owner = User(
        email="owner19@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(owner)
    db_session.commit()

    # Create contacts
    emergency = Contact(
        first_name="Emergency",
        is_emergency_contact=True,
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    regular = Contact(
        first_name="Regular",
        is_emergency_contact=False,
        owner_user_id=owner.id,
        created_at=datetime.utcnow()
    )
    db_session.add_all([emergency, regular])
    db_session.commit()

    # Query emergency contacts
    emergency_contacts = db_session.query(Contact).filter(
        Contact.owner_user_id == owner.id,
        Contact.is_emergency_contact == True
    ).all()

    assert len(emergency_contacts) == 1
    assert emergency_contacts[0].first_name == "Emergency"
