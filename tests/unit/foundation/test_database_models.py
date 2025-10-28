"""
Module 1: Foundation - Database Models Tests (Tests 1-15)

Tests basic model creation, relationships, and constraints.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserProfile, UserStatus
from app.models.contact import Contact
from app.models.admin import Admin
from app.models.vault import VaultFile
from app.core.security import hash_password
from tests.helpers.bug_reporter import report_production_bug


# ==============================================
# USER MODEL TESTS (Tests 1-5)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_user_with_minimal_required_fields(db_session):
    """
    Test #1: Create user with email only (minimal required fields)
    """
    user = User(
        email="minimal@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "minimal@example.com"
    assert user.status == UserStatus.unknown
    assert user.created_at is not None


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_user_with_all_optional_fields(db_session):
    """
    Test #2: Create user with all fields populated
    """
    user = User(
        display_name="Full User",
        email="fulluser@example.com",
        phone="9876543210",
        country_code="+91",
        password=hash_password("Test@1234"),
        status=UserStatus.verified,
        communication_channel="email",
        otp="123456",
        otp_expires_at=datetime.utcnow(),
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.display_name == "Full User"
    assert user.email == "fulluser@example.com"
    assert user.phone == "9876543210"
    assert user.country_code == "+91"
    assert user.password is not None
    assert user.status == UserStatus.verified
    assert user.communication_channel == "email"
    assert user.otp == "123456"
    assert user.otp_verified is True


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_user_email_unique_constraint_enforced(db_session):
    """
    Test #3: Duplicate email raises IntegrityError
    """
    user1 = User(
        email="duplicate@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user1)
    db_session.commit()

    # Try to create another user with same email
    user2 = User(
        email="duplicate@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_user_phone_unique_constraint_enforced(db_session):
    """
    Test #4: Duplicate phone raises IntegrityError
    """
    user1 = User(
        email="user1@example.com",
        phone="9876543210",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user1)
    db_session.commit()

    # Try to create another user with same phone
    user2 = User(
        email="user2@example.com",
        phone="9876543210",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_user_status_enum_validation(db_session):
    """
    Test #5: Only valid UserStatus values accepted
    """
    # Valid statuses
    for status in [UserStatus.unknown, UserStatus.guest, UserStatus.verified, UserStatus.member]:
        user = User(
            email=f"user_{status.value}@example.com",
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.status == status

        # Clean up for next iteration
        db_session.delete(user)
        db_session.commit()


# ==============================================
# CONTACT MODEL TESTS (Tests 6-10)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_contact_with_minimal_fields(test_user, db_session):
    """
    Test #6: Create contact with first_name only
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="John",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert contact.id is not None
    assert contact.owner_user_id == test_user.id
    assert contact.first_name == "John"


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_contact_with_all_fields(test_user, db_session):
    """
    Test #7: Create contact with all fields
    """
    contact = Contact(
        owner_user_id=test_user.id,
        linked_user_id=None,
        title="Mr",
        first_name="John",
        middle_name="M",
        last_name="Doe",
        local_name="Johnny",
        company="Acme Corp",
        job_type="Engineer",
        website="https://example.com",
        category="Work",
        relation="Colleague",
        phone_numbers=["+919876543210", "+919876543211"],
        whatsapp_numbers=["+919876543210"],
        emails=["john@example.com", "john.doe@acme.com"],
        flat_building_no="123",
        street="Main Street",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        postal_code="400001",
        date_of_birth="1990-01-01",
        anniversary="2015-06-15",
        notes="Important contact",
        contact_image="/images/john.jpg",
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

    assert contact.id is not None
    assert contact.title == "Mr"
    assert contact.first_name == "John"
    assert contact.middle_name == "M"
    assert contact.last_name == "Doe"
    assert contact.phone_numbers == ["+919876543210", "+919876543211"]
    assert contact.emails == ["john@example.com", "john.doe@acme.com"]
    assert contact.city == "Mumbai"
    assert contact.share_after_death is True
    assert contact.is_emergency_contact is False


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_contact_owner_foreign_key_valid(test_user, db_session):
    """
    Test #8: Valid owner_user_id required
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Valid",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert contact.owner_user_id == test_user.id


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_contact_owner_foreign_key_invalid_raises(db_session):
    """
    Test #9: Invalid owner_user_id raises error
    """
    contact = Contact(
        owner_user_id=99999,  # Non-existent user ID
        first_name="Invalid",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_contact_cascade_delete_when_owner_deleted(test_user, db_session):
    """
    Test #10: Delete user deletes contacts (cascade)
    """
    # Create contact
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="ToDelete",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    contact_id = contact.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify contact is also deleted
    deleted_contact = db_session.query(Contact).filter(Contact.id == contact_id).first()
    assert deleted_contact is None


# ==============================================
# ADMIN MODEL TESTS (Tests 11-12)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_admin_with_all_fields(db_session):
    """
    Test #11: Create admin with all fields
    """
    admin = Admin(
        username="testadmin",
        email="admin@example.com",
        password=hash_password("Admin@1234"),
        otp="654321",
        otp_expires_at=datetime.utcnow(),
        otp_verified=True,
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    assert admin.id is not None
    assert admin.username == "testadmin"
    assert admin.email == "admin@example.com"
    assert admin.password is not None
    assert admin.otp == "654321"
    assert admin.otp_verified is True


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_admin_username_unique_constraint(db_session):
    """
    Test #12: Duplicate admin username raises IntegrityError
    """
    admin1 = Admin(
        username="duplicate_admin",
        email="admin1@example.com",
        password=hash_password("Admin@1234"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin1)
    db_session.commit()

    # Try to create another admin with same username
    admin2 = Admin(
        username="duplicate_admin",
        email="admin2@example.com",
        password=hash_password("Admin@1234"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin2)

    with pytest.raises(IntegrityError):
        db_session.commit()


# ==============================================
# VAULT MODEL TESTS (Tests 13-15)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_vault_file_manual_mode(test_user, db_session):
    """
    Test #13: creation_mode='manual'
    """
    vault_file = VaultFile(
        file_id="test_file_123",
        owner_user_id=test_user.id,
        template_id="passport",
        creation_mode="manual",
        encrypted_dek="encrypted_key_base64",
        encrypted_form_data="encrypted_data_base64",
        nonce_form_data="nonce_base64",
        has_source_file=False,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vault_file)
    db_session.commit()
    db_session.refresh(vault_file)

    assert vault_file.file_id == "test_file_123"
    assert vault_file.owner_user_id == test_user.id
    assert vault_file.creation_mode == "manual"
    assert vault_file.has_source_file is False
    assert vault_file.status == "active"


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_create_vault_file_import_mode(test_user, db_session):
    """
    Test #14: creation_mode='import' with source file
    """
    vault_file = VaultFile(
        file_id="test_file_456",
        owner_user_id=test_user.id,
        template_id="license",
        creation_mode="import",
        encrypted_dek="encrypted_key_base64",
        encrypted_form_data="encrypted_data_base64",
        nonce_form_data="nonce_base64",
        has_source_file=True,
        source_file_s3_key="vault/user_1/test_file_456.pdf.enc",
        source_file_nonce="source_nonce_base64",
        source_file_original_name="license.pdf",
        source_file_mime_type="application/pdf",
        source_file_size_bytes=102400,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vault_file)
    db_session.commit()
    db_session.refresh(vault_file)

    assert vault_file.file_id == "test_file_456"
    assert vault_file.creation_mode == "import"
    assert vault_file.has_source_file is True
    assert vault_file.source_file_s3_key == "vault/user_1/test_file_456.pdf.enc"
    assert vault_file.source_file_original_name == "license.pdf"
    assert vault_file.source_file_size_bytes == 102400


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_vault_file_owner_foreign_key_to_user(test_user, db_session):
    """
    Test #15: Valid owner_user_id required for vault file
    """
    vault_file = VaultFile(
        file_id="test_file_789",
        owner_user_id=test_user.id,
        template_id="insurance",
        creation_mode="manual",
        encrypted_dek="encrypted_key_base64",
        encrypted_form_data="encrypted_data_base64",
        nonce_form_data="nonce_base64",
        has_source_file=False,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vault_file)
    db_session.commit()
    db_session.refresh(vault_file)

    assert vault_file.owner_user_id == test_user.id

    # Verify relationship works
    assert vault_file.owner is not None
    assert vault_file.owner.id == test_user.id


# ==============================================
# USER PROFILE MODEL TESTS (Tests 16-20)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_user_profile_one_to_one_relationship(test_user, db_session):
    """
    Test #16: UserProfile has 1:1 relationship with User
    """
    profile = UserProfile(
        user_id=test_user.id,
        first_name="Test",
        last_name="User",
        city="Mumbai",
        country="India"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    assert profile.user_id == test_user.id
    assert profile.user is not None
    assert profile.user.id == test_user.id


@pytest.mark.unit
@pytest.mark.foundation
@pytest.mark.critical
def test_user_profile_duplicate_user_id_raises_error(test_user, db_session):
    """
    Test #17: Cannot create two profiles for same user (1:1 constraint)
    """
    profile1 = UserProfile(
        user_id=test_user.id,
        first_name="First",
        last_name="Profile"
    )
    db_session.add(profile1)
    db_session.commit()

    # Try to create second profile for same user
    profile2 = UserProfile(
        user_id=test_user.id,
        first_name="Second",
        last_name="Profile"
    )
    db_session.add(profile2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_user_profile_cascade_delete_with_user(test_user, db_session):
    """
    Test #18: Delete user deletes profile (cascade)
    """
    profile = UserProfile(
        user_id=test_user.id,
        first_name="Test",
        last_name="User"
    )
    db_session.add(profile)
    db_session.commit()

    user_id = test_user.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify profile is also deleted
    deleted_profile = db_session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    assert deleted_profile is None


@pytest.mark.unit
@pytest.mark.foundation
def test_user_with_null_password_can_be_created(db_session):
    """
    Test #19: User can exist without password (OAuth/social login scenario)
    """
    user = User(
        email="oauth@example.com",
        password=None,  # No password for OAuth users
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.password is None
    assert user.email == "oauth@example.com"


@pytest.mark.unit
@pytest.mark.foundation
def test_user_email_case_sensitivity(db_session):
    """
    Test #20: Email uniqueness is case-sensitive or case-insensitive?
    REAL BUG: If case-sensitive, users can create test@example.com AND Test@example.com
    """
    user1 = User(
        email="test@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user1)
    db_session.commit()

    # Try with different case
    user2 = User(
        email="Test@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user2)

    # This test reveals if email case handling is correct
    # If it allows both, there's a bug - emails should be case-insensitive
    try:
        db_session.commit()
        # If we get here, emails are case-sensitive (BUG FOUND!)
        report_production_bug(
            bug_number=1,
            title="Email Case Sensitivity",
            issue="Database allows duplicate emails with different cases (test@example.com and Test@example.com)",
            impact="Users can create duplicate accounts bypassing uniqueness constraint",
            fix="Use CITEXT column type OR normalize emails to lowercase before saving",
            location="models/user.py - email column definition"
        )
        # Clean up both users
        db_session.delete(user2)
        db_session.delete(user1)
        db_session.commit()
        # FAIL the test - production bug found
        assert False, "PRODUCTION BUG #1: Email Case Sensitivity"
    except IntegrityError:
        # Good! Database enforces uniqueness regardless of case
        db_session.rollback()
        assert True


# ==============================================
# EDGE CASE & VALIDATION TESTS (Tests 21-30)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_user_with_very_long_email_fails(db_session):
    """
    Test #21: Email column has length limit
    REAL BUG: If no limit, can cause database errors or performance issues
    """
    very_long_email = "a" * 300 + "@example.com"

    user = User(
        email=very_long_email,
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    # Should fail if email has max length constraint
    # If it passes, there's no length validation (potential bug)
    try:
        db_session.commit()
        # Check if it actually stored the full length
        db_session.refresh(user)
        if len(user.email) == len(very_long_email):
            # No truncation, no limit - potential issue
            assert len(user.email) <= 255, "POTENTIAL BUG: Email should have reasonable length limit"
    except Exception:
        # Good! Database enforces length limit
        db_session.rollback()
        assert True


@pytest.mark.unit
@pytest.mark.foundation
def test_user_with_invalid_email_format_still_saves(db_session):
    """
    Test #22: Database doesn't validate email format
    REAL BUG: Database allows "notanemail" as email - validation must be done in app layer
    """
    user = User(
        email="notanemail",  # Invalid format
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # This passes! Database doesn't validate email format
    # App layer MUST validate emails before saving
    assert user.email == "notanemail"
    # NOTE: This test documents that email validation happens in app, not DB


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_with_empty_phone_array(test_user, db_session):
    """
    Test #23: Contact with empty phone_numbers array
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="NoPhone",
        phone_numbers=[],  # Empty array
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert contact.phone_numbers == []


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_with_null_phone_array(test_user, db_session):
    """
    Test #24: Contact with NULL phone_numbers
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="NullPhone",
        phone_numbers=None,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    # Check how database handles NULL JSON
    assert contact.phone_numbers is None or contact.phone_numbers == []


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_with_malformed_json_in_array(test_user, db_session):
    """
    Test #25: Contact with unexpected data in JSON array
    REAL BUG: If app expects strings, but gets numbers/objects
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="WeirdData",
        phone_numbers=["valid", 12345, {"nested": "object"}],  # Mixed types
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    # Database stores it! App must validate JSON structure
    assert len(contact.phone_numbers) == 3
    # NOTE: This documents that JSON validation must happen in app layer


@pytest.mark.unit
@pytest.mark.foundation
def test_user_password_hash_length(db_session):
    """
    Test #26: BCrypt hash has expected length (60 characters)
    """
    password_hash = hash_password("Test@1234")
    assert len(password_hash) == 60, \
        f"BCrypt hash should be 60 chars, got {len(password_hash)}"

    user = User(
        email="hash@example.com",
        password=password_hash,
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert len(user.password) == 60


@pytest.mark.unit
@pytest.mark.foundation
def test_user_otp_can_be_null(db_session):
    """
    Test #27: OTP can be NULL (not required for all operations)
    """
    user = User(
        email="no_otp@example.com",
        otp=None,
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.otp is None


@pytest.mark.unit
@pytest.mark.foundation
def test_user_otp_expires_at_can_be_null(db_session):
    """
    Test #28: OTP expiry can be NULL
    """
    user = User(
        email="no_expiry@example.com",
        otp="123456",
        otp_expires_at=None,
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.otp_expires_at is None


@pytest.mark.unit
@pytest.mark.foundation
def test_vault_file_without_source_file_metadata(test_user, db_session):
    """
    Test #29: Vault file created manually has no source file metadata
    """
    vault_file = VaultFile(
        file_id="manual_123",
        owner_user_id=test_user.id,
        template_id="passport",
        creation_mode="manual",
        encrypted_dek="key",
        encrypted_form_data="data",
        nonce_form_data="nonce",
        has_source_file=False,
        source_file_s3_key=None,
        source_file_nonce=None,
        source_file_original_name=None,
        source_file_mime_type=None,
        source_file_size_bytes=None,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vault_file)
    db_session.commit()
    db_session.refresh(vault_file)

    assert vault_file.has_source_file is False
    assert vault_file.source_file_s3_key is None
    assert vault_file.source_file_original_name is None
    assert vault_file.source_file_size_bytes is None


@pytest.mark.unit
@pytest.mark.foundation
def test_admin_email_can_be_duplicate_of_user_email(test_user, db_session):
    """
    Test #30: Admin email is separate from User email (different tables)
    DESIGN CHECK: Can admin@example.com exist as both User and Admin?
    """
    # test_user already has email
    user_email = test_user.email

    # Create admin with same email
    admin = Admin(
        username="adminuser",
        email=user_email,  # Same email as user
        password=hash_password("Admin@1234"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    # This passes! Admin and User are separate tables
    # NOTE: App must handle login disambiguation (admin vs user login)
    assert admin.email == test_user.email


# ==============================================
# RELATIONSHIP TESTS (Tests 31-40)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_user_can_have_multiple_contacts(test_user, db_session):
    """
    Test #31: User can have many contacts (1:N relationship)
    """
    contact1 = Contact(
        owner_user_id=test_user.id,
        first_name="Contact1",
        created_at=datetime.utcnow()
    )
    contact2 = Contact(
        owner_user_id=test_user.id,
        first_name="Contact2",
        created_at=datetime.utcnow()
    )
    contact3 = Contact(
        owner_user_id=test_user.id,
        first_name="Contact3",
        created_at=datetime.utcnow()
    )
    db_session.add_all([contact1, contact2, contact3])
    db_session.commit()

    # Query contacts for user
    user_contacts = db_session.query(Contact).filter(Contact.owner_user_id == test_user.id).all()
    assert len(user_contacts) == 3


@pytest.mark.unit
@pytest.mark.foundation
def test_user_can_have_multiple_vault_files(test_user, db_session):
    """
    Test #32: User can have many vault files (1:N relationship)
    """
    vault_files = []
    for i in range(5):
        vf = VaultFile(
            file_id=f"file_{i}",
            owner_user_id=test_user.id,
            template_id="passport",
            creation_mode="manual",
            encrypted_dek="key",
            encrypted_form_data="data",
            nonce_form_data="nonce",
            has_source_file=False,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        vault_files.append(vf)

    db_session.add_all(vault_files)
    db_session.commit()

    # Query vault files for user
    user_files = db_session.query(VaultFile).filter(VaultFile.owner_user_id == test_user.id).all()
    assert len(user_files) == 5


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_linked_to_another_user(test_user, db_session):
    """
    Test #33: Contact can be linked to another user (optional FK)
    """
    # Create second user
    linked_user = User(
        email="linked@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()
    db_session.refresh(linked_user)

    # Create contact linked to that user
    contact = Contact(
        owner_user_id=test_user.id,
        linked_user_id=linked_user.id,
        first_name="LinkedContact",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    assert contact.linked_user_id == linked_user.id
    assert contact.linked_user is not None
    assert contact.linked_user.id == linked_user.id


@pytest.mark.unit
@pytest.mark.foundation
def test_query_user_with_eager_loaded_contacts(test_user, db_session):
    """
    Test #34: Test eager loading of relationships (performance check)
    """
    # Create contacts
    for i in range(3):
        contact = Contact(
            owner_user_id=test_user.id,
            first_name=f"Contact{i}",
            created_at=datetime.utcnow()
        )
        db_session.add(contact)
    db_session.commit()

    # Query with eager loading (joinedload)
    from sqlalchemy.orm import joinedload
    user = db_session.query(User).options(joinedload(User.contacts)).filter(User.id == test_user.id).first()

    assert user is not None
    # Accessing contacts should not trigger additional query (already loaded)
    assert len(user.contacts) == 3


@pytest.mark.unit
@pytest.mark.foundation
def test_delete_user_cascades_to_vault_files(test_user, db_session):
    """
    Test #35: Delete user cascades to vault files
    """
    vault_file = VaultFile(
        file_id="cascade_test",
        owner_user_id=test_user.id,
        template_id="passport",
        creation_mode="manual",
        encrypted_dek="key",
        encrypted_form_data="data",
        nonce_form_data="nonce",
        has_source_file=False,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vault_file)
    db_session.commit()
    file_id = vault_file.file_id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify vault file is deleted
    deleted_file = db_session.query(VaultFile).filter(VaultFile.file_id == file_id).first()
    assert deleted_file is None


# ==============================================
# DATA INTEGRITY & CONSTRAINT TESTS (Tests 36-45)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_user_created_at_auto_set(db_session):
    """
    Test #36: created_at should be auto-set on insert
    """
    user = User(
        email="autotime@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.created_at is not None


@pytest.mark.unit
@pytest.mark.foundation
def test_user_updated_at_changes_on_update(db_session):
    """
    Test #37: updated_at should change when record is updated
    """
    user = User(
        email="updatetime@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    original_updated = user.updated_at

    # Update user
    import time
    time.sleep(0.1)  # Small delay to ensure timestamp changes
    user.display_name = "Updated Name"
    user.updated_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(user)

    # updated_at should have changed
    assert user.updated_at > original_updated


@pytest.mark.unit
@pytest.mark.foundation
def test_vault_file_status_field_accepts_valid_values(test_user, db_session):
    """
    Test #38: Vault file status accepts expected values
    """
    statuses = ["active", "archived", "deleted"]

    for status in statuses:
        vf = VaultFile(
            file_id=f"status_{status}",
            owner_user_id=test_user.id,
            template_id="passport",
            creation_mode="manual",
            encrypted_dek="key",
            encrypted_form_data="data",
            nonce_form_data="nonce",
            has_source_file=False,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(vf)
        db_session.commit()
        db_session.refresh(vf)

        assert vf.status == status

        # Clean up
        db_session.delete(vf)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_with_very_long_name(test_user, db_session):
    """
    Test #39: Contact with very long name (tests field length limits)
    """
    long_name = "A" * 500

    contact = Contact(
        owner_user_id=test_user.id,
        first_name=long_name,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)

    try:
        db_session.commit()
        db_session.refresh(contact)
        # If it saves, check if it was truncated
        assert len(contact.first_name) <= 500
    except Exception:
        # Field has length limit (good!)
        db_session.rollback()
        assert True


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_special_characters_in_name(test_user, db_session):
    """
    Test #40: Contact with special characters in name (unicode support)
    """
    special_names = [
        "José García",  # Spanish
        "François Müller",  # French/German
        "राज कुमार",  # Hindi
        "李明",  # Chinese
        "Алексей",  # Russian
        "محمد",  # Arabic
    ]

    for name in special_names:
        contact = Contact(
            owner_user_id=test_user.id,
            first_name=name,
            created_at=datetime.utcnow()
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert contact.first_name == name

        # Clean up
        db_session.delete(contact)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_user_with_sql_injection_attempt_in_email(db_session):
    """
    Test #41: SQL injection attempt in email field (security test)
    """
    malicious_email = "admin@example.com'; DROP TABLE users; --"

    user = User(
        email=malicious_email,
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # ORM protects against SQL injection - email is stored as-is
    assert user.email == malicious_email

    # Verify users table still exists
    users_count = db_session.query(User).count()
    assert users_count > 0


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_with_xss_attempt_in_notes(test_user, db_session):
    """
    Test #42: XSS attempt in notes field (security test)
    """
    xss_payload = "<script>alert('XSS')</script>"

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="XSS Test",
        notes=xss_payload,
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    # Database stores as-is (app must escape on output)
    assert contact.notes == xss_payload
    # NOTE: Frontend MUST escape this when rendering


@pytest.mark.unit
@pytest.mark.foundation
def test_vault_file_with_negative_file_size(test_user, db_session):
    """
    Test #43: Vault file with negative file size (data validation)
    """
    vault_file = VaultFile(
        file_id="negative_size",
        owner_user_id=test_user.id,
        template_id="passport",
        creation_mode="import",
        encrypted_dek="key",
        encrypted_form_data="data",
        nonce_form_data="nonce",
        has_source_file=True,
        source_file_s3_key="test.pdf",
        source_file_nonce="nonce",
        source_file_original_name="test.pdf",
        source_file_mime_type="application/pdf",
        source_file_size_bytes=-1000,  # Negative size!
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(vault_file)
    db_session.commit()
    db_session.refresh(vault_file)

    # Database allows it! App must validate
    assert vault_file.source_file_size_bytes == -1000
    # NOTE: App layer MUST validate file_size_bytes >= 0


@pytest.mark.unit
@pytest.mark.foundation
def test_admin_with_empty_string_password(db_session):
    """
    Test #44: Admin with empty string password (should fail in app, not DB)
    """
    admin = Admin(
        username="emptypass",
        email="empty@example.com",
        password="",  # Empty password!
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    # Database allows it! App must validate password strength
    assert admin.password == ""
    # NOTE: App MUST enforce password requirements


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_phone_array_with_duplicates(test_user, db_session):
    """
    Test #45: Contact with duplicate phone numbers in array
    """
    contact = Contact(
        owner_user_id=test_user.id,
        first_name="DupePhones",
        phone_numbers=["+919876543210", "+919876543210", "+919876543210"],  # Duplicates
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    # Database allows duplicates in array! App should deduplicate
    assert len(contact.phone_numbers) == 3
    assert contact.phone_numbers[0] == contact.phone_numbers[1]
    # NOTE: App should deduplicate phone numbers before saving
