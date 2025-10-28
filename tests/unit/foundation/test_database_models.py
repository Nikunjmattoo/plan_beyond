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
from app.models.vault import VaultFile, VaultFileAccess
from core.security import hash_password


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
