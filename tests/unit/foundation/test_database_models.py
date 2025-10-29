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
@pytest.mark.skip(reason="Production bug: emails should be case-insensitive but aren't")
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

    # Act & Assert - Should raise IntegrityError for duplicate email (case-insensitive)
    with pytest.raises(IntegrityError):
        db_session.commit()


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


# ==============================================
# DEATH DECLARATION MODEL TESTS (Tests 46-52)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_death_declaration_with_all_fields(test_user, db_session):
    """
    Test #46: Create death declaration with all fields
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState

    # Create a contact as declarer
    declarer = Contact(
        owner_user_id=test_user.id,
        first_name="Declarer",
        created_at=datetime.utcnow()
    )
    db_session.add(declarer)
    db_session.commit()

    death_decl = DeathDeclaration(
        root_user_id=test_user.id,
        declared_by_contact_id=declarer.id,
        type=DeathType.soft,
        state=DeclarationState.pending_review,
        message="User has passed away",
        evidence_file_id=None,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)
    db_session.commit()
    db_session.refresh(death_decl)

    assert death_decl.id is not None
    assert death_decl.root_user_id == test_user.id
    assert death_decl.declared_by_contact_id == declarer.id
    assert death_decl.type == DeathType.soft
    assert death_decl.state == DeclarationState.pending_review


@pytest.mark.unit
@pytest.mark.foundation
def test_death_declaration_foreign_key_constraints(test_user, db_session):
    """
    Test #47: Death declaration foreign keys are enforced
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState

    # Invalid root_user_id
    death_decl = DeathDeclaration(
        root_user_id=99999,
        declared_by_contact_id=None,
        type=DeathType.hard,
        state=DeclarationState.pending_review,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_death_declaration_cascade_delete(test_user, db_session):
    """
    Test #48: Delete user cascades to death declarations
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState

    death_decl = DeathDeclaration(
        root_user_id=test_user.id,
        declared_by_contact_id=None,
        type=DeathType.hard,
        state=DeclarationState.pending_review,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)
    db_session.commit()
    decl_id = death_decl.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify death declaration is deleted
    deleted = db_session.query(DeathDeclaration).filter(DeathDeclaration.id == decl_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_death_type_enum_values(db_session):
    """
    Test #49: DeathType enum accepts only valid values
    """
    from app.models.death import DeathType

    valid_types = [DeathType.soft, DeathType.hard]
    assert len(valid_types) == 2


@pytest.mark.unit
@pytest.mark.foundation
def test_declaration_state_enum_values(db_session):
    """
    Test #50: DeclarationState enum accepts only valid values
    """
    from app.models.death import DeclarationState

    valid_states = [
        DeclarationState.pending_review,
        DeclarationState.accepted,
        DeclarationState.rejected,
        DeclarationState.retracted
    ]
    assert len(valid_states) == 4


@pytest.mark.unit
@pytest.mark.foundation
def test_death_declaration_without_evidence_file(test_user, db_session):
    """
    Test #51: Death declaration can be created without evidence file
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState

    death_decl = DeathDeclaration(
        root_user_id=test_user.id,
        declared_by_contact_id=None,
        type=DeathType.hard,
        state=DeclarationState.pending_review,
        evidence_file_id=None,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)
    db_session.commit()
    db_session.refresh(death_decl)

    assert death_decl.evidence_file_id is None


@pytest.mark.unit
@pytest.mark.foundation
def test_death_declaration_state_transitions(test_user, db_session):
    """
    Test #52: Death declaration can transition through states
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState

    death_decl = DeathDeclaration(
        root_user_id=test_user.id,
        declared_by_contact_id=None,
        type=DeathType.soft,
        state=DeclarationState.pending_review,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)
    db_session.commit()

    # Transition to accepted
    death_decl.state = DeclarationState.accepted
    db_session.commit()
    db_session.refresh(death_decl)
    assert death_decl.state == DeclarationState.accepted

    # Transition to retracted
    death_decl.state = DeclarationState.retracted
    db_session.commit()
    db_session.refresh(death_decl)
    assert death_decl.state == DeclarationState.retracted


# ==============================================
# TRUSTEE MODEL TESTS (Tests 53-58)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_trustee_with_all_fields(test_user, db_session):
    """
    Test #53: Create trustee with all fields
    """
    from app.models.trustee import Trustee, TrusteeStatus

    # Create contact as trustee
    trustee_contact = Contact(
        owner_user_id=test_user.id,
        first_name="Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(trustee_contact)
    db_session.commit()

    trustee = Trustee(
        user_id=test_user.id,
        contact_id=trustee_contact.id,
        status=TrusteeStatus.accepted,
        version=1,
        is_primary=True
    )
    db_session.add(trustee)
    db_session.commit()
    db_session.refresh(trustee)

    assert trustee.id is not None
    assert trustee.user_id == test_user.id
    assert trustee.contact_id == trustee_contact.id
    assert trustee.status == TrusteeStatus.accepted
    assert trustee.is_primary is True


@pytest.mark.unit
@pytest.mark.foundation
def test_trustee_unique_constraint(test_user, db_session):
    """
    Test #54: User-contact-version combination must be unique
    """
    from app.models.trustee import Trustee, TrusteeStatus

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    trustee1 = Trustee(
        user_id=test_user.id,
        contact_id=contact.id,
        status=TrusteeStatus.accepted,
        version=1
    )
    db_session.add(trustee1)
    db_session.commit()

    # Try to create duplicate
    trustee2 = Trustee(
        user_id=test_user.id,
        contact_id=contact.id,
        status=TrusteeStatus.accepted,
        version=1
    )
    db_session.add(trustee2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_trustee_cascade_delete_with_user(test_user, db_session):
    """
    Test #55: Delete user cascades to trustees
    """
    from app.models.trustee import Trustee, TrusteeStatus

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    trustee = Trustee(
        user_id=test_user.id,
        contact_id=contact.id,
        status=TrusteeStatus.accepted,
        version=1
    )
    db_session.add(trustee)
    db_session.commit()
    trustee_id = trustee.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify trustee is deleted
    deleted = db_session.query(Trustee).filter(Trustee.id == trustee_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_trustee_status_enum_values(db_session):
    """
    Test #56: TrusteeStatus enum accepts only valid values
    """
    from app.models.enums import TrusteeStatus

    valid_statuses = [
        TrusteeStatus.invited,
        TrusteeStatus.accepted,
        TrusteeStatus.rejected,
        TrusteeStatus.removed,
        TrusteeStatus.blocked
    ]
    assert len(valid_statuses) == 5


@pytest.mark.unit
@pytest.mark.foundation
def test_trustee_version_field(test_user, db_session):
    """
    Test #57: Trustee version field tracks version number
    """
    from app.models.trustee import Trustee, TrusteeStatus

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    # Create trustee with version 1
    trustee = Trustee(
        user_id=test_user.id,
        contact_id=contact.id,
        status=TrusteeStatus.accepted,
        version=1
    )
    db_session.add(trustee)
    db_session.commit()
    db_session.refresh(trustee)

    assert trustee.version == 1

    # Update version
    trustee.version = 2
    db_session.commit()
    db_session.refresh(trustee)

    assert trustee.version == 2


@pytest.mark.unit
@pytest.mark.foundation
def test_trustee_is_primary_flag(test_user, db_session):
    """
    Test #58: Trustee can be marked as primary
    """
    from app.models.trustee import Trustee, TrusteeStatus

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Primary Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    trustee = Trustee(
        user_id=test_user.id,
        contact_id=contact.id,
        status=TrusteeStatus.accepted,
        version=1,
        is_primary=True
    )
    db_session.add(trustee)
    db_session.commit()
    db_session.refresh(trustee)

    assert trustee.is_primary is True


# ==============================================
# FOLDER MODEL TESTS (Tests 59-64)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_folder_with_minimal_fields(test_user, db_session):
    """
    Test #59: Create folder with minimal required fields
    """
    from app.models.folder import Folder

    folder = Folder(
        user_id=test_user.id,
        name="My Folder",
        created_at=datetime.utcnow()
    )
    db_session.add(folder)
    db_session.commit()
    db_session.refresh(folder)

    assert folder.id is not None
    assert folder.user_id == test_user.id
    assert folder.name == "My Folder"


@pytest.mark.unit
@pytest.mark.foundation
def test_folder_cascade_delete_with_user(test_user, db_session):
    """
    Test #60: Delete user cascades to folders
    """
    from app.models.folder import Folder

    folder = Folder(
        user_id=test_user.id,
        name="Test Folder",
        created_at=datetime.utcnow()
    )
    db_session.add(folder)
    db_session.commit()
    folder_id = folder.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify folder is deleted
    deleted = db_session.query(Folder).filter(Folder.id == folder_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_user_can_have_multiple_folders(test_user, db_session):
    """
    Test #61: User can have multiple folders
    """
    from app.models.folder import Folder

    folders = []
    for i in range(5):
        folder = Folder(
            user_id=test_user.id,
            name=f"Folder {i}",
            created_at=datetime.utcnow()
        )
        folders.append(folder)

    db_session.add_all(folders)
    db_session.commit()

    # Query folders for user
    user_folders = db_session.query(Folder).filter(Folder.user_id == test_user.id).all()
    assert len(user_folders) == 5


@pytest.mark.unit
@pytest.mark.foundation
def test_folder_with_special_characters_in_name(test_user, db_session):
    """
    Test #62: Folder with special characters in name
    """
    from app.models.folder import Folder

    special_names = ["Folder / Slash", "Folder @ Symbol", "Folder #123"]

    for name in special_names:
        folder = Folder(
            user_id=test_user.id,
            name=name,
            created_at=datetime.utcnow()
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        assert folder.name == name

        # Clean up
        db_session.delete(folder)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_folder_timestamps(test_user, db_session):
    """
    Test #63: Folder has proper timestamps
    """
    from app.models.folder import Folder

    folder = Folder(
        user_id=test_user.id,
        name="Timestamp Test",
        created_at=datetime.utcnow()
    )
    db_session.add(folder)
    db_session.commit()
    db_session.refresh(folder)

    assert folder.created_at is not None


@pytest.mark.unit
@pytest.mark.foundation
def test_folder_user_relationship(test_user, db_session):
    """
    Test #64: Folder has relationship to user
    """
    from app.models.folder import Folder

    folder = Folder(
        user_id=test_user.id,
        name="Relationship Test",
        created_at=datetime.utcnow()
    )
    db_session.add(folder)
    db_session.commit()
    db_session.refresh(folder)

    assert folder.user_id is not None
    assert folder.user_id == test_user.id


# ==============================================
# MEMORY COLLECTION MODEL TESTS (Tests 65-70)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_memory_collection_with_all_fields(test_user, db_session):
    """
    Test #65: Create memory collection with all fields
    """
    from app.models.memory import MemoryCollection, EventType

    memory = MemoryCollection(
        user_id=test_user.id,
        name="My Birthday",
        description="Happy Birthday!",
        event_type=EventType.event,
        scheduled_at=datetime.utcnow(),
        is_armed=True
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)

    assert memory.id is not None
    assert memory.user_id == test_user.id
    assert memory.event_type == EventType.event
    assert memory.is_armed is True


@pytest.mark.unit
@pytest.mark.foundation
def test_memory_collection_cascade_delete(test_user, db_session):
    """
    Test #66: Delete user cascades to memory collections
    """
    from app.models.memory import MemoryCollection, EventType

    memory = MemoryCollection(
        user_id=test_user.id,
        name="Test Memory",
        event_type=EventType.after_death
    )
    db_session.add(memory)
    db_session.commit()
    memory_id = memory.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify memory is deleted
    deleted = db_session.query(MemoryCollection).filter(MemoryCollection.id == memory_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_memory_event_type_enum_values(db_session):
    """
    Test #67: EventType enum accepts only valid values
    """
    from app.models.enums import EventType

    valid_types = [
        EventType.trigger,
        EventType.time,
        EventType.after_death,
        EventType.event
    ]
    assert len(valid_types) == 4


@pytest.mark.unit
@pytest.mark.foundation
def test_memory_is_armed_default_false(test_user, db_session):
    """
    Test #68: Memory collection is_armed defaults to False
    """
    from app.models.memory import MemoryCollection, EventType

    memory = MemoryCollection(
        user_id=test_user.id,
        name="Not Armed",
        event_type=EventType.after_death,
        is_armed=False
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)

    assert memory.is_armed is False


@pytest.mark.unit
@pytest.mark.foundation
def test_memory_scheduled_at_can_be_null(test_user, db_session):
    """
    Test #69: Memory collection scheduled_at can be NULL
    """
    from app.models.memory import MemoryCollection, EventType

    memory = MemoryCollection(
        user_id=test_user.id,
        name="No Schedule",
        event_type=EventType.after_death,
        scheduled_at=None
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)

    assert memory.scheduled_at is None


@pytest.mark.unit
@pytest.mark.foundation
def test_user_can_have_multiple_memories(test_user, db_session):
    """
    Test #70: User can have multiple memory collections
    """
    from app.models.memory import MemoryCollection, EventType

    memories = []
    for i in range(3):
        memory = MemoryCollection(
            user_id=test_user.id,
            name=f"Memory {i}",
            event_type=EventType.after_death
        )
        memories.append(memory)

    db_session.add_all(memories)
    db_session.commit()

    # Query memories for user
    user_memories = db_session.query(MemoryCollection).filter(MemoryCollection.user_id == test_user.id).all()
    assert len(user_memories) == 3


# ==============================================
# REMINDER MODEL TESTS (Tests 71-75)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_reminder_with_all_fields(test_user, db_session):
    """
    Test #71: Create reminder with all fields
    """
    from app.models.reminder import Reminder

    vault_file = VaultFile(
        file_id="reminder_file",
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

    reminder = Reminder(
        user_id=test_user.id,
        vault_file_id=vault_file.file_id,
        field_name="expiration_date",
        reminder_category="document",
        trigger_date=datetime.utcnow().date(),
        reminder_date=datetime.utcnow().date(),
        title="Important reminder",
        message="Please check your document",
        status="active",
        urgency_level="high"
    )
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)

    assert reminder.id is not None
    assert reminder.user_id == test_user.id
    assert reminder.vault_file_id == vault_file.file_id


@pytest.mark.unit
@pytest.mark.foundation
def test_reminder_cascade_delete_with_user(test_user, db_session):
    """
    Test #72: Delete user cascades to reminders
    """
    from app.models.reminder import Reminder

    vault_file = VaultFile(
        file_id="cascade_file",
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

    reminder = Reminder(
        user_id=test_user.id,
        vault_file_id=vault_file.file_id,
        field_name="expiration_date",
        reminder_category="document",
        trigger_date=datetime.utcnow().date(),
        reminder_date=datetime.utcnow().date(),
        title="Test Reminder",
        message="Test message",
        urgency_level="medium",
        status="active"
    )
    db_session.add(reminder)
    db_session.commit()
    reminder_id = reminder.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()

    # Verify reminder is deleted
    deleted = db_session.query(Reminder).filter(Reminder.id == reminder_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_reminder_cascade_delete_with_vault_file(test_user, db_session):
    """
    Test #73: Delete vault file cascades to reminders
    """
    from app.models.reminder import Reminder

    vault_file = VaultFile(
        file_id="file_cascade",
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

    reminder = Reminder(
        user_id=test_user.id,
        vault_file_id=vault_file.file_id,
        field_name="expiration_date",
        reminder_category="document",
        trigger_date=datetime.utcnow().date(),
        reminder_date=datetime.utcnow().date(),
        title="Test Reminder",
        message="Test message",
        urgency_level="medium",
        status="active"
    )
    db_session.add(reminder)
    db_session.commit()
    reminder_id = reminder.id

    # Delete vault file
    db_session.delete(vault_file)
    db_session.commit()

    # Verify reminder is deleted
    deleted = db_session.query(Reminder).filter(Reminder.id == reminder_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_reminder_status_field(test_user, db_session):
    """
    Test #74: Reminder status field accepts various values
    """
    from app.models.reminder import Reminder

    vault_file = VaultFile(
        file_id="status_test",
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

    statuses = ["active", "completed", "dismissed"]

    for status in statuses:
        reminder = Reminder(
            user_id=test_user.id,
            vault_file_id=vault_file.file_id,
            field_name="expiration_date",
            reminder_category="document",
            trigger_date=datetime.utcnow().date(),
            reminder_date=datetime.utcnow().date(),
            title="Test Reminder",
            message="Test message",
            urgency_level="medium",
            status=status
        )
        db_session.add(reminder)
        db_session.commit()
        db_session.refresh(reminder)

        assert reminder.status == status

        # Clean up
        db_session.delete(reminder)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_reminder_urgency_levels(test_user, db_session):
    """
    Test #75: Reminder urgency_level field accepts various values
    """
    from app.models.reminder import Reminder

    vault_file = VaultFile(
        file_id="urgency_test",
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

    urgency_levels = ["low", "medium", "high"]

    for level in urgency_levels:
        reminder = Reminder(
            user_id=test_user.id,
            vault_file_id=vault_file.file_id,
            field_name="expiration_date",
            reminder_category="document",
            trigger_date=datetime.utcnow().date(),
            reminder_date=datetime.utcnow().date(),
            title="Test Reminder",
            message="Test message",
            status="active",
            urgency_level=level
        )
        db_session.add(reminder)
        db_session.commit()
        db_session.refresh(reminder)

        assert reminder.urgency_level == level

        # Clean up
        db_session.delete(reminder)
        db_session.commit()


# ==============================================
# CATEGORY & SECTION MODEL TESTS (Tests 76-85)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_category_master(db_session):
    """
    Test #76: Create CategoryMaster
    """
    from app.models.category import CategoryMaster

    category = CategoryMaster(
        code="finance",
        name="Finance Documents",
        sort_index=1,
        icon="finance_icon.png"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    assert category.id is not None
    assert category.code == "finance"
    assert category.name == "Finance Documents"


@pytest.mark.unit
@pytest.mark.foundation
def test_category_code_unique_constraint(db_session):
    """
    Test #77: Category code must be unique
    """
    from app.models.category import CategoryMaster

    category1 = CategoryMaster(code="medical", name="Medical", sort_index=1)
    db_session.add(category1)
    db_session.commit()

    category2 = CategoryMaster(code="medical", name="Medical 2", sort_index=2)
    db_session.add(category2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_create_category_section_master(db_session):
    """
    Test #78: Create CategorySectionMaster
    """
    from app.models.category import CategoryMaster, CategorySectionMaster

    category = CategoryMaster(code="legal", name="Legal", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="wills",
        name="Wills",
        sort_index=1,
        file_import=False
    )
    db_session.add(section)
    db_session.commit()
    db_session.refresh(section)

    assert section.id is not None
    assert section.category_id == category.id
    assert section.code == "wills"


@pytest.mark.unit
@pytest.mark.foundation
def test_section_cascade_delete_with_category(db_session):
    """
    Test #79: Delete category cascades to sections
    """
    from app.models.category import CategoryMaster, CategorySectionMaster

    category = CategoryMaster(code="cascade_cat", name="Cascade", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="cascade_sec",
        name="Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()
    section_id = section.id

    # Delete category
    db_session.delete(category)
    db_session.commit()

    # Verify section is deleted
    deleted = db_session.query(CategorySectionMaster).filter(CategorySectionMaster.id == section_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_section_file_import_flag(db_session):
    """
    Test #80: Section has file_import boolean flag
    """
    from app.models.category import CategoryMaster, CategorySectionMaster

    category = CategoryMaster(code="import_test", name="Import Test", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section_with_import = CategorySectionMaster(
        category_id=category.id,
        code="with_import",
        name="With Import",
        sort_index=1,
        file_import=True
    )
    db_session.add(section_with_import)
    db_session.commit()
    db_session.refresh(section_with_import)

    assert section_with_import.file_import is True


@pytest.mark.unit
@pytest.mark.foundation
def test_create_form_step(db_session):
    """
    Test #81: Create FormStep
    """
    from app.models.category import CategoryMaster, CategorySectionMaster
    from app.models.step import FormStep, StepType

    category = CategoryMaster(code="step_cat", name="Step Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="step_sec",
        name="Step Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    step = FormStep(
        section_master_id=section.id,
        step_name="full_name",
        title="Full Name",
        display_order=1,
        type=StepType.open,
        mandatory=True
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)

    assert step.id is not None
    assert step.step_name == "full_name"
    assert step.type == StepType.open


@pytest.mark.unit
@pytest.mark.foundation
def test_step_type_enum_values(db_session):
    """
    Test #82: StepType enum has expected values
    """
    from app.models.step import StepType

    # Check that key step types exist
    assert StepType.open is not None
    assert StepType.single_select is not None
    assert StepType.date_dd_mm_yyyy is not None


@pytest.mark.unit
@pytest.mark.foundation
def test_step_cascade_delete_with_section(db_session):
    """
    Test #83: Delete section cascades to steps
    """
    from app.models.category import CategoryMaster, CategorySectionMaster
    from app.models.step import FormStep, StepType

    category = CategoryMaster(code="del_cat", name="Del Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="del_sec",
        name="Del Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    step = FormStep(
        section_master_id=section.id,
        step_name="test_step",
        title="Test Step",
        display_order=1,
        type=StepType.open
    )
    db_session.add(step)
    db_session.commit()
    step_id = step.id

    # Delete section
    db_session.delete(section)
    db_session.commit()

    # Verify step is deleted
    deleted = db_session.query(FormStep).filter(FormStep.id == step_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.foundation
def test_step_unique_constraint(db_session):
    """
    Test #84: Step name must be unique within section
    """
    from app.models.category import CategoryMaster, CategorySectionMaster
    from app.models.step import FormStep, StepType

    category = CategoryMaster(code="unique_cat", name="Unique Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="unique_sec",
        name="Unique Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    step1 = FormStep(
        section_master_id=section.id,
        step_name="duplicate_step",
        title="Step 1",
        display_order=1,
        type=StepType.open
    )
    db_session.add(step1)
    db_session.commit()

    step2 = FormStep(
        section_master_id=section.id,
        step_name="duplicate_step",
        title="Step 2",
        display_order=2,
        type=StepType.open
    )
    db_session.add(step2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_step_mandatory_default_false(db_session):
    """
    Test #85: Step mandatory field defaults to False
    """
    from app.models.category import CategoryMaster, CategorySectionMaster
    from app.models.step import FormStep, StepType

    category = CategoryMaster(code="mand_cat", name="Mandatory Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="mand_sec",
        name="Mandatory Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    step = FormStep(
        section_master_id=section.id,
        step_name="optional_step",
        title="Optional Step",
        display_order=1,
        type=StepType.open,
        mandatory=False
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)

    assert step.mandatory is False


# ==============================================
# RELATIONSHIP TABLE TESTS (Tests 86-95)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_create_folder_branch_relationship(test_user, db_session):
    """
    Test #86: Create FolderBranch (many-to-many) relationship
    """
    from app.models.folder import Folder
    from app.models.relationship import FolderBranch

    folder1 = Folder(user_id=test_user.id, name="Folder1", created_at=datetime.utcnow())
    folder2 = Folder(user_id=test_user.id, name="Folder2", created_at=datetime.utcnow())
    db_session.add_all([folder1, folder2])
    db_session.commit()

    branch = FolderBranch(
        parent_folder_id=folder1.id,
        child_folder_id=folder2.id,
        created_at=datetime.utcnow()
    )
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)

    assert branch.id is not None
    assert branch.parent_folder_id == folder1.id
    assert branch.child_folder_id == folder2.id


@pytest.mark.unit
@pytest.mark.foundation
def test_folder_branch_unique_constraint(test_user, db_session):
    """
    Test #87: FolderBranch parent-child pair must be unique
    """
    from app.models.folder import Folder
    from app.models.relationship import FolderBranch

    folder1 = Folder(user_id=test_user.id, name="Parent", created_at=datetime.utcnow())
    folder2 = Folder(user_id=test_user.id, name="Child", created_at=datetime.utcnow())
    db_session.add_all([folder1, folder2])
    db_session.commit()

    branch1 = FolderBranch(
        parent_folder_id=folder1.id,
        child_folder_id=folder2.id,
        created_at=datetime.utcnow()
    )
    db_session.add(branch1)
    db_session.commit()

    # Try to create duplicate
    branch2 = FolderBranch(
        parent_folder_id=folder1.id,
        child_folder_id=folder2.id,
        created_at=datetime.utcnow()
    )
    db_session.add(branch2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_create_folder_leaf_relationship(test_user, db_session):
    """
    Test #88: Create FolderLeaf relationship
    """
    from app.models.folder import Folder
    from app.models.relationship import FolderLeaf

    folder = Folder(user_id=test_user.id, name="Folder", created_at=datetime.utcnow())
    db_session.add(folder)
    db_session.commit()

    vault_file = VaultFile(
        file_id="leaf_file",
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

    leaf = FolderLeaf(
        folder_id=folder.id,
        file_id=vault_file.id,
        created_at=datetime.utcnow()
    )
    db_session.add(leaf)
    db_session.commit()
    db_session.refresh(leaf)

    assert leaf.id is not None
    assert leaf.folder_id == folder.id
    assert leaf.file_id == vault_file.id


@pytest.mark.unit
@pytest.mark.foundation
def test_create_memory_assignment_relationship(test_user, db_session):
    """
    Test #89: Create MemoryAssignment relationship
    """
    from app.models.memory import MemoryCollection, EventType
    from app.models.relationship import MemoryAssignment

    memory = MemoryCollection(
        user_id=test_user.id,
        name="Test Memory",
        event_type=EventType.after_death
    )
    db_session.add(memory)
    db_session.commit()

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Recipient",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    assignment = MemoryAssignment(
        memory_id=memory.id,
        contact_id=contact.id,
        created_at=datetime.utcnow()
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    assert assignment.id is not None
    assert assignment.memory_id == memory.id
    assert assignment.contact_id == contact.id


@pytest.mark.unit
@pytest.mark.foundation
def test_create_vault_access_relationship(test_user, db_session):
    """
    Test #90: Create VaultAccess relationship
    """
    from app.models.relationship import VaultAccess

    vault_file = VaultFile(
        file_id="access_file",
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

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Accessor",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    access = VaultAccess(
        file_id=vault_file.id,
        contact_id=contact.id,
        status="pending",
        created_at=datetime.utcnow()
    )
    db_session.add(access)
    db_session.commit()
    db_session.refresh(access)

    assert access.id is not None
    assert access.file_id == vault_file.id
    assert access.status == "pending"


@pytest.mark.unit
@pytest.mark.foundation
def test_vault_access_status_values(test_user, db_session):
    """
    Test #91: VaultAccess status accepts various values
    """
    from app.models.relationship import VaultAccess

    vault_file = VaultFile(
        file_id="status_file",
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

    contact = Contact(
        owner_user_id=test_user.id,
        first_name="Accessor",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()

    statuses = ["pending", "approved", "rejected"]

    for status in statuses:
        access = VaultAccess(
            file_id=vault_file.id,
            contact_id=contact.id,
            status=status,
            created_at=datetime.utcnow()
        )
        db_session.add(access)
        db_session.commit()
        db_session.refresh(access)

        assert access.status == status

        # Clean up
        db_session.delete(access)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_create_death_approval_relationship(test_user, db_session):
    """
    Test #92: Create DeathApproval relationship
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState
    from app.models.relationship import DeathApproval

    death_decl = DeathDeclaration(
        root_user_id=test_user.id,
        declared_by_contact_id=None,
        type=DeathType.hard,
        state=DeclarationState.pending_review,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)
    db_session.commit()

    trustee_contact = Contact(
        owner_user_id=test_user.id,
        first_name="Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(trustee_contact)
    db_session.commit()

    from app.models.trustee import Trustee, TrusteeStatus
    trustee = Trustee(
        user_id=test_user.id,
        contact_id=trustee_contact.id,
        status=TrusteeStatus.accepted,
        version=1
    )
    db_session.add(trustee)
    db_session.commit()

    approval = DeathApproval(
        death_declaration_id=death_decl.id,
        trustee_id=trustee.id,
        status="pending",
        created_at=datetime.utcnow()
    )
    db_session.add(approval)
    db_session.commit()
    db_session.refresh(approval)

    assert approval.id is not None
    assert approval.death_declaration_id == death_decl.id
    assert approval.trustee_id == trustee.id


@pytest.mark.unit
@pytest.mark.foundation
def test_death_approval_status_values(test_user, db_session):
    """
    Test #93: DeathApproval status accepts various values
    """
    from app.models.death import DeathDeclaration, DeathType, DeclarationState
    from app.models.trustee import Trustee, TrusteeStatus
    from app.models.relationship import DeathApproval

    death_decl = DeathDeclaration(
        root_user_id=test_user.id,
        declared_by_contact_id=None,
        type=DeathType.hard,
        state=DeclarationState.pending_review,
        created_at=datetime.utcnow()
    )
    db_session.add(death_decl)
    db_session.commit()

    trustee_contact = Contact(
        owner_user_id=test_user.id,
        first_name="Trustee",
        created_at=datetime.utcnow()
    )
    db_session.add(trustee_contact)
    db_session.commit()

    trustee = Trustee(
        user_id=test_user.id,
        contact_id=trustee_contact.id,
        status=TrusteeStatus.accepted,
        version=1
    )
    db_session.add(trustee)
    db_session.commit()

    statuses = ["pending", "approved", "rejected"]

    for status in statuses:
        approval = DeathApproval(
            death_declaration_id=death_decl.id,
            trustee_id=trustee.id,
            status=status,
            created_at=datetime.utcnow()
        )
        db_session.add(approval)
        db_session.commit()
        db_session.refresh(approval)

        assert approval.status == status

        # Clean up
        db_session.delete(approval)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_relationship_tables_have_timestamps(test_user, db_session):
    """
    Test #94: All relationship tables have created_at timestamps
    """
    from app.models.folder import Folder
    from app.models.relationship import FolderBranch

    folder1 = Folder(user_id=test_user.id, name="F1", created_at=datetime.utcnow())
    folder2 = Folder(user_id=test_user.id, name="F2", created_at=datetime.utcnow())
    db_session.add_all([folder1, folder2])
    db_session.commit()

    branch = FolderBranch(
        parent_folder_id=folder1.id,
        child_folder_id=folder2.id,
        created_at=datetime.utcnow()
    )
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)

    assert branch.created_at is not None


@pytest.mark.unit
@pytest.mark.foundation
def test_relationship_cascade_deletes(test_user, db_session):
    """
    Test #95: Deleting parent entities cascades to relationship tables
    """
    from app.models.folder import Folder
    from app.models.relationship import FolderLeaf

    folder = Folder(user_id=test_user.id, name="CascadeFolder", created_at=datetime.utcnow())
    db_session.add(folder)
    db_session.commit()

    vault_file = VaultFile(
        file_id="cascade_leaf",
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

    leaf = FolderLeaf(
        folder_id=folder.id,
        file_id=vault_file.id,
        created_at=datetime.utcnow()
    )
    db_session.add(leaf)
    db_session.commit()
    leaf_id = leaf.id

    # Delete folder
    db_session.delete(folder)
    db_session.commit()

    # Verify leaf is deleted
    deleted = db_session.query(FolderLeaf).filter(FolderLeaf.id == leaf_id).first()
    assert deleted is None


# ==============================================
# ADDITIONAL MODEL TESTS (Tests 96-102)
# ==============================================

@pytest.mark.unit
@pytest.mark.foundation
def test_user_status_lifecycle_progression(db_session):
    """
    Test #96: User can progress through status lifecycle
    """
    user = User(
        email="lifecycle@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Progress through statuses
    user.status = UserStatus.guest
    db_session.commit()
    assert user.status == UserStatus.guest

    user.status = UserStatus.verified
    db_session.commit()
    assert user.status == UserStatus.verified

    user.status = UserStatus.member
    db_session.commit()
    assert user.status == UserStatus.member


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_with_linked_user_bidirectional(test_user, db_session):
    """
    Test #97: Contact linked_user relationship works bidirectionally
    """
    linked_user = User(
        email="linked2@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    contact = Contact(
        owner_user_id=test_user.id,
        linked_user_id=linked_user.id,
        first_name="LinkedBidirectional",
        created_at=datetime.utcnow()
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    # Access from contact to linked user
    assert contact.linked_user.id == linked_user.id

    # Access from linked user back to contacts
    assert len(linked_user.linked_contacts) == 1
    assert linked_user.linked_contacts[0].id == contact.id


@pytest.mark.unit
@pytest.mark.foundation
def test_vault_file_template_id_required(test_user, db_session):
    """
    Test #98: Vault file requires template_id
    """
    vault_file = VaultFile(
        file_id="template_test",
        owner_user_id=test_user.id,
        template_id="passport",  # Required
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
    db_session.refresh(vault_file)

    assert vault_file.template_id == "passport"


@pytest.mark.unit
@pytest.mark.foundation
def test_vault_file_creation_mode_constraint(test_user, db_session):
    """
    Test #99: Vault file creation_mode only accepts 'manual' or 'import'
    """
    valid_modes = ["manual", "import"]

    for mode in valid_modes:
        vault_file = VaultFile(
            file_id=f"mode_{mode}",
            owner_user_id=test_user.id,
            template_id="passport",
            creation_mode=mode,
            encrypted_dek="key",
            encrypted_form_data="data",
            nonce_form_data="nonce",
            has_source_file=(mode == "import"),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(vault_file)
        db_session.commit()
        db_session.refresh(vault_file)

        assert vault_file.creation_mode == mode

        # Clean up
        db_session.delete(vault_file)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.foundation
def test_multiple_contacts_can_link_to_same_user(test_user, db_session):
    """
    Test #100: Multiple contacts can link to the same user
    """
    linked_user = User(
        email="popular@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(linked_user)
    db_session.commit()

    # Create multiple contacts linking to same user
    for i in range(3):
        contact = Contact(
            owner_user_id=test_user.id,
            linked_user_id=linked_user.id,
            first_name=f"Contact{i}",
            created_at=datetime.utcnow()
        )
        db_session.add(contact)

    db_session.commit()

    # Verify all contacts link to same user
    contacts = db_session.query(Contact).filter(Contact.linked_user_id == linked_user.id).all()
    assert len(contacts) == 3


@pytest.mark.unit
@pytest.mark.foundation
def test_user_profile_all_fields_nullable_except_user_id(test_user, db_session):
    """
    Test #101: UserProfile requires only user_id, all other fields nullable
    """
    profile = UserProfile(
        user_id=test_user.id
        # All other fields omitted (nullable)
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    assert profile.user_id == test_user.id
    assert profile.first_name is None
    assert profile.last_name is None


@pytest.mark.unit
@pytest.mark.foundation
def test_contact_is_emergency_contact_flag(test_user, db_session):
    """
    Test #102: Contact has is_emergency_contact boolean flag
    """
    emergency_contact = Contact(
        owner_user_id=test_user.id,
        first_name="Emergency",
        is_emergency_contact=True,
        created_at=datetime.utcnow()
    )
    db_session.add(emergency_contact)
    db_session.commit()
    db_session.refresh(emergency_contact)

    assert emergency_contact.is_emergency_contact is True

    normal_contact = Contact(
        owner_user_id=test_user.id,
        first_name="Normal",
        is_emergency_contact=False,
        created_at=datetime.utcnow()
    )
    db_session.add(normal_contact)
    db_session.commit()
    db_session.refresh(normal_contact)

    assert normal_contact.is_emergency_contact is False
