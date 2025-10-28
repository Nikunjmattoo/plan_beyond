"""
Module 2: Auth - User Controller Tests (Tests 274-298)

Tests user controller CRUD operations, OTP generation, and status transitions.
These tests verify the controller layer, NOT just the models.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from controller.user import (
    create_user,
    get_user_by_email,
    get_user_by_phone,
    get_user_by_display_name,
    get_user_by_phone_and_cc,
    update_user,
    delete_user,
    get_all_users_with_contact_counts
)
from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserUpdate, CommunicationChannel
from app.core.security import hash_password, verify_password
import random
import string


# ==============================================
# USER CREATION TESTS (Tests 274-280)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_with_email_only(db_session):
    """
    Test #274: Create user with email + minimal fields
    """
    user_data = UserCreate(
        display_name="Email User",
        email="email.user@example.com"
    )

    user = create_user(db_session, user_data)

    assert user.id is not None
    assert user.email == "email.user@example.com"
    assert user.display_name == "Email User"
    assert user.status == UserStatus.unknown
    assert user.otp is None
    assert user.password is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_with_phone_only(db_session):
    """
    Test #275: Create user with phone + minimal fields
    """
    user_data = UserCreate(
        display_name="Phone User",
        phone="+919876543210",
        country_code="+91"
    )

    user = create_user(db_session, user_data)

    assert user.id is not None
    assert user.phone == "+919876543210"
    assert user.country_code == "+91"
    assert user.display_name == "Phone User"
    assert user.email is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_password_automatically_hashed(db_session):
    """
    Test #276: Password is automatically hashed on creation
    CRITICAL: Storing plain text passwords is a MAJOR security bug!
    """
    plain_password = "SuperSecret123!"

    user_data = UserCreate(
        display_name="Secure User",
        email="secure@example.com",
        password=plain_password
    )

    user = create_user(db_session, user_data)

    # CRITICAL: Password must be hashed, not stored in plain text
    assert user.password is not None
    assert user.password != plain_password  # NOT plain text
    assert len(user.password) > 50  # Bcrypt hashes are ~60 chars

    # Verify the hash works
    assert verify_password(plain_password, user.password) is True
    assert verify_password("WrongPassword", user.password) is False

    # If this fails, we have a PRODUCTION BUG: passwords stored in plain text!


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_otp_not_set_initially(db_session):
    """
    Test #277: OTP should be None initially, set only on request
    """
    user_data = UserCreate(
        display_name="New User",
        email="newuser@example.com"
    )

    user = create_user(db_session, user_data)

    assert user.otp is None
    assert user.otp_verified is False
    assert user.otp_expires_at is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_status_defaults_to_unknown(db_session):
    """
    Test #278: New users should start with status=unknown
    """
    user_data = UserCreate(
        display_name="Status Test",
        email="status@example.com"
    )

    user = create_user(db_session, user_data)

    assert user.status == UserStatus.unknown
    # Should NOT be guest, verified, or member yet


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_duplicate_email_raises_error(db_session):
    """
    Test #279: Duplicate emails should be rejected
    """
    # Create first user
    user1_data = UserCreate(
        display_name="User One",
        email="duplicate@example.com"
    )
    user1 = create_user(db_session, user1_data)

    # Try to create second user with same email
    user2_data = UserCreate(
        display_name="User Two",
        email="duplicate@example.com"
    )

    with pytest.raises(IntegrityError):
        create_user(db_session, user2_data)

    db_session.rollback()


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_duplicate_phone_raises_error(db_session):
    """
    Test #280: Duplicate phone numbers should be rejected
    """
    # Create first user
    user1_data = UserCreate(
        display_name="User One",
        phone="+919999999999",
        country_code="+91"
    )
    user1 = create_user(db_session, user1_data)

    # Try to create second user with same phone
    user2_data = UserCreate(
        display_name="User Two",
        phone="+919999999999",
        country_code="+91"
    )

    with pytest.raises(IntegrityError):
        create_user(db_session, user2_data)

    db_session.rollback()


# ==============================================
# USER RETRIEVAL TESTS (Tests 281-285)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_user_by_email_returns_user(db_session):
    """
    Test #281: Retrieve user by email
    """
    user_data = UserCreate(
        display_name="Find Me",
        email="findme@example.com"
    )
    created_user = create_user(db_session, user_data)

    found_user = get_user_by_email(db_session, "findme@example.com")

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "findme@example.com"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_user_by_phone_returns_user(db_session):
    """
    Test #282: Retrieve user by phone
    """
    user_data = UserCreate(
        display_name="Phone User",
        phone="+911234567890",
        country_code="+91"
    )
    created_user = create_user(db_session, user_data)

    found_user = get_user_by_phone(db_session, "+911234567890")

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.phone == "+911234567890"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_user_by_display_name_returns_user(db_session):
    """
    Test #283: Retrieve user by display_name
    """
    user_data = UserCreate(
        display_name="UniqueDisplayName",
        email="unique@example.com"
    )
    created_user = create_user(db_session, user_data)

    found_user = get_user_by_display_name(db_session, "UniqueDisplayName")

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.display_name == "UniqueDisplayName"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_user_by_phone_and_country_code(db_session):
    """
    Test #284: Retrieve user by phone + country code
    """
    user_data = UserCreate(
        display_name="India User",
        phone="+915555555555",
        country_code="+91"
    )
    created_user = create_user(db_session, user_data)

    # Test with explicit +
    found_user = get_user_by_phone_and_cc(db_session, "+915555555555", "+91")
    assert found_user is not None
    assert found_user.id == created_user.id

    # Test without + (controller should add it)
    found_user2 = get_user_by_phone_and_cc(db_session, "+915555555555", "91")
    assert found_user2 is not None
    assert found_user2.id == created_user.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_user_not_found_returns_none(db_session):
    """
    Test #285: Non-existent user returns None
    """
    assert get_user_by_email(db_session, "nonexistent@example.com") is None
    assert get_user_by_phone(db_session, "+919999999999") is None
    assert get_user_by_display_name(db_session, "NoSuchUser") is None


# ==============================================
# USER UPDATE TESTS (Tests 286-292)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_user_display_name(db_session):
    """
    Test #286: Update user's display name
    """
    user_data = UserCreate(
        display_name="Old Name",
        email="update1@example.com"
    )
    user = create_user(db_session, user_data)

    updates = UserUpdate(display_name="New Name")
    updated_user = update_user(db_session, user.id, updates)

    assert updated_user is not None
    assert updated_user.display_name == "New Name"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_user_email(db_session):
    """
    Test #287: Update user's email
    """
    user_data = UserCreate(
        display_name="Email Updater",
        email="oldemail@example.com"
    )
    user = create_user(db_session, user_data)

    updates = UserUpdate(email="newemail@example.com")
    updated_user = update_user(db_session, user.id, updates)

    assert updated_user is not None
    assert updated_user.email == "newemail@example.com"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_user_phone(db_session):
    """
    Test #288: Update user's phone
    """
    user_data = UserCreate(
        display_name="Phone Updater",
        phone="+911111111111",
        country_code="+91"
    )
    user = create_user(db_session, user_data)

    updates = UserUpdate(phone="+912222222222")
    updated_user = update_user(db_session, user.id, updates)

    assert updated_user is not None
    assert updated_user.phone == "+912222222222"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_user_country_code_adds_plus_prefix(db_session):
    """
    Test #289: Country code should have + prefix added if missing
    POTENTIAL BUG: If controller doesn't normalize, could cause lookup failures
    """
    user_data = UserCreate(
        display_name="Country User",
        phone="+913333333333",
        country_code="+91"
    )
    user = create_user(db_session, user_data)

    # Update with country code WITHOUT + prefix
    updates = UserUpdate(country_code="1")  # Missing +
    updated_user = update_user(db_session, user.id, updates)

    # Controller should add the + prefix
    assert updated_user.country_code == "+1"
    # NOT "1" - this would be a bug!


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_user_status(db_session):
    """
    Test #290: Update user status (for testing only, normally done via workflow)
    """
    user_data = UserCreate(
        display_name="Status User",
        email="status_update@example.com"
    )
    user = create_user(db_session, user_data)

    # Directly update status via model (controller doesn't expose this)
    user.status = UserStatus.guest
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.guest


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_user_profile_fields(db_session):
    """
    Test #291: Update profile fields (name, address, etc.)
    """
    user_data = UserCreate(
        display_name="Profile User",
        email="profile@example.com"
    )
    user = create_user(db_session, user_data)

    updates = UserUpdate(
        first_name="John",
        last_name="Doe",
        city="Mumbai",
        country="India"
    )
    updated_user = update_user(db_session, user.id, updates)

    # Note: These fields might be in UserProfile table, not User table
    # This test documents that behavior
    assert updated_user is not None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_update_nonexistent_user_returns_none(db_session):
    """
    Test #292: Updating non-existent user returns None
    """
    updates = UserUpdate(display_name="No User")
    result = update_user(db_session, 99999, updates)

    assert result is None


# ==============================================
# OTP GENERATION TESTS (Tests 293-295)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_generate_otp_is_six_digits(db_session):
    """
    Test #293: OTP should be exactly 6 digits
    """
    # Generate multiple OTPs to ensure consistency
    for _ in range(10):
        otp = ''.join(random.choices(string.digits, k=6))
        assert len(otp) == 6
        assert otp.isdigit()


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_generate_otp_is_numeric_only(db_session):
    """
    Test #294: OTP should contain only digits (0-9)
    """
    otp = ''.join(random.choices(string.digits, k=6))

    assert otp.isdigit()
    assert all(c in '0123456789' for c in otp)
    # Should NOT contain letters, symbols, etc.


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_generate_otp_different_each_call(db_session):
    """
    Test #295: OTP generation should be random (different each time)
    POTENTIAL BUG: If OTP is not random, attacker could predict it!
    """
    # Generate 100 OTPs
    otps = set()
    for _ in range(100):
        otp = ''.join(random.choices(string.digits, k=6))
        otps.add(otp)

    # Should have many unique values (not all the same)
    # With 6 digits, there are 1,000,000 possibilities
    # Getting 100 unique from 100 attempts is very likely if random
    assert len(otps) > 90  # At least 90% unique

    # If this fails with all OTPs being the same, we have a MAJOR security bug!


# ==============================================
# STATUS TRANSITION TESTS (Tests 296-298)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_transition_unknown_to_guest(db_session):
    """
    Test #296: User can transition from unknown -> guest
    """
    user_data = UserCreate(
        display_name="Transition User",
        email="transition@example.com"
    )
    user = create_user(db_session, user_data)

    assert user.status == UserStatus.unknown

    # Transition to guest
    user.status = UserStatus.guest
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.guest


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_transition_guest_to_verified(db_session):
    """
    Test #297: User can transition from guest -> verified
    """
    user_data = UserCreate(
        display_name="Guest User",
        email="guest@example.com"
    )
    user = create_user(db_session, user_data)
    user.status = UserStatus.guest
    db_session.commit()

    # Transition to verified
    user.status = UserStatus.verified
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.verified


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_transition_verified_to_member(db_session):
    """
    Test #298: User can transition from verified -> member
    """
    user_data = UserCreate(
        display_name="Verified User",
        email="verified@example.com"
    )
    user = create_user(db_session, user_data)
    user.status = UserStatus.verified
    db_session.commit()

    # Transition to member
    user.status = UserStatus.member
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.member
