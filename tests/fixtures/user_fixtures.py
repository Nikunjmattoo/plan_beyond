"""
User, admin, contact, and profile fixtures.
"""
import pytest
from datetime import datetime
from typing import Optional

from app.models.user import User, UserProfile, UserStatus
from app.models.admin import Admin
from app.models.contact import Contact
from app.core.security import hash_password


# ==============================================
# USER FIXTURES
# ==============================================

@pytest.fixture
def test_user(db_session) -> User:
    """
    Create a test user with status 'verified'.
    """
    user = User(
        display_name="Test User",
        email="testuser@example.com",
        phone="9876543210",
        country_code="+91",
        password=hash_password("Test@1234"),
        status=UserStatus.verified,
        communication_channel="email",
        otp=None,
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_with_profile(db_session) -> User:
    """
    Create a test user with complete profile.
    """
    user = User(
        display_name="Test User Profile",
        email="userprofile@example.com",
        phone="9876543211",
        country_code="+91",
        password=hash_password("Test@1234"),
        status=UserStatus.member,
        communication_channel="email",
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.flush()

    # Create profile
    profile = UserProfile(
        user_id=user.id,
        title="Mr",
        first_name="Test",
        middle_name="M",
        last_name="User",
        date_of_birth="1990-01-01",
        gender="Male",
        address_line_1="123 Test Street",
        city="Mumbai",
        state="Maharashtra",
        zip_code="400001",
        country="India",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def test_user_guest(db_session) -> User:
    """
    Create a test user with status 'guest' (OTP verified but not document verified).
    """
    user = User(
        display_name="Guest User",
        email="guest@example.com",
        phone="9876543212",
        country_code="+91",
        password=hash_password("Test@1234"),
        status=UserStatus.guest,
        communication_channel="email",
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_unknown(db_session) -> User:
    """
    Create a test user with status 'unknown' (just registered, OTP not verified).
    """
    user = User(
        display_name="Unknown User",
        email="unknown@example.com",
        phone="9876543213",
        country_code="+91",
        password=hash_password("Test@1234"),
        status=UserStatus.unknown,
        communication_channel="email",
        otp="123456",
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_test_user(db_session) -> User:
    """
    Create a second test user for sharing/collaboration tests.
    """
    user = User(
        display_name="Second User",
        email="seconduser@example.com",
        phone="9876543214",
        country_code="+91",
        password=hash_password("Test@1234"),
        status=UserStatus.verified,
        communication_channel="email",
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================
# ADMIN FIXTURES
# ==============================================

@pytest.fixture
def test_admin(db_session) -> Admin:
    """
    Create a test admin user.
    """
    admin = Admin(
        username="testadmin",
        email="admin@example.com",
        password=hash_password("Admin@1234"),
        otp=None,
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


# ==============================================
# CONTACT FIXTURES
# ==============================================

@pytest.fixture
def test_contact(db_session, test_user) -> Contact:
    """
    Create a test contact for the test user.
    """
    contact = Contact(
        owner_user_id=test_user.id,
        linked_user_id=None,
        title="Mr",
        first_name="John",
        last_name="Doe",
        phone_numbers=["+919876543215"],
        emails=["john.doe@example.com"],
        relation="Friend",
        category="Personal",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture
def test_contact_linked(db_session, test_user, second_test_user) -> Contact:
    """
    Create a contact that is linked to another user in the system.
    """
    contact = Contact(
        owner_user_id=test_user.id,
        linked_user_id=second_test_user.id,
        title="Ms",
        first_name="Jane",
        last_name="Smith",
        phone_numbers=["+919876543216"],
        emails=["jane.smith@example.com"],
        relation="Friend",
        category="Personal",
        share_after_death=True,
        is_emergency_contact=False,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture
def emergency_contact(db_session, test_user) -> Contact:
    """
    Create an emergency contact.
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Emergency",
        last_name="Contact",
        phone_numbers=["+919876543217"],
        emails=["emergency@example.com"],
        relation="Family",
        category="Emergency",
        is_emergency_contact=True,
        share_after_death=True,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


# ==============================================
# BULK USER CREATION
# ==============================================

@pytest.fixture
def multiple_users(db_session) -> list[User]:
    """
    Create multiple test users for bulk operation tests.
    """
    users = []
    for i in range(5):
        user = User(
            display_name=f"User {i}",
            email=f"user{i}@example.com",
            phone=f"987654320{i}",
            country_code="+91",
            password=hash_password("Test@1234"),
            status=UserStatus.verified,
            communication_channel="email",
            otp_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(user)
        users.append(user)

    db_session.commit()
    for user in users:
        db_session.refresh(user)

    return users


@pytest.fixture
def multiple_contacts(db_session, test_user) -> list[Contact]:
    """
    Create multiple contacts for the test user.
    """
    contacts = []
    for i in range(5):
        contact = Contact(
            owner_user_id=test_user.id,
            first_name=f"Contact{i}",
            last_name="Test",
            phone_numbers=[f"+91987654321{i}"],
            emails=[f"contact{i}@example.com"],
            relation="Friend",
            category="Personal",
            created_at=datetime.utcnow()
        )
        db_session.add(contact)
        contacts.append(contact)

    db_session.commit()
    for contact in contacts:
        db_session.refresh(contact)

    return contacts


__all__ = [
    "test_user",
    "test_user_with_profile",
    "test_user_guest",
    "test_user_unknown",
    "second_test_user",
    "test_admin",
    "test_contact",
    "test_contact_linked",
    "emergency_contact",
    "multiple_users",
    "multiple_contacts",
]
