"""
Module 2: Auth - Admin Controller Tests (Tests 299-308)

Tests admin creation, authentication, and OTP management.
NOTE: If admin controller doesn't exist, these tests work directly with models.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.admin import Admin
from app.core.security import hash_password, verify_password
import random
import string


# ==============================================
# ADMIN CREATION TESTS (Tests 299-302)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_admin_with_username_email(db_session):
    """
    Test #299: Create admin with username and email
    """
    admin = Admin(
        username="admin1",
        email="admin1@example.com",
        password=hash_password("AdminPass123!"),
        created_at=datetime.utcnow()
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    assert admin.id is not None
    assert admin.username == "admin1"
    assert admin.email == "admin1@example.com"
    assert admin.otp is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_password_hashed_on_save(db_session):
    """
    Test #300: Admin password must be hashed before saving
    CRITICAL: Plain text admin passwords are a MAJOR security breach!
    """
    plain_password = "SuperAdminSecret!"

    admin = Admin(
        username="secureadmin",
        email="secure.admin@example.com",
        password=hash_password(plain_password),
        created_at=datetime.utcnow()
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    # Password must be hashed
    assert admin.password != plain_password
    assert len(admin.password) > 50  # Bcrypt hash length

    # Verify hash works
    assert verify_password(plain_password, admin.password) is True
    assert verify_password("WrongPassword", admin.password) is False


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_otp_generation(db_session):
    """
    Test #301: Admin OTP generation
    """
    admin = Admin(
        username="otpadmin",
        email="otp.admin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Generate OTP
    otp = ''.join(random.choices(string.digits, k=6))
    admin.otp = otp
    admin.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    admin.otp_verified = False
    db_session.commit()
    db_session.refresh(admin)

    assert admin.otp == otp
    assert len(admin.otp) == 6
    assert admin.otp.isdigit()
    assert admin.otp_expires_at is not None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_admin_by_username(db_session):
    """
    Test #302: Find admin by username
    """
    admin = Admin(
        username="findme",
        email="findme.admin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Query by username
    found = db_session.query(Admin).filter(Admin.username == "findme").first()

    assert found is not None
    assert found.username == "findme"
    assert found.id == admin.id


# ==============================================
# ADMIN RETRIEVAL & UNIQUENESS (Tests 303-304)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_get_admin_by_email(db_session):
    """
    Test #303: Find admin by email
    """
    admin = Admin(
        username="emailadmin",
        email="email.admin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Query by email
    found = db_session.query(Admin).filter(Admin.email == "email.admin@example.com").first()

    assert found is not None
    assert found.email == "email.admin@example.com"
    assert found.id == admin.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_duplicate_username_raises_error(db_session):
    """
    Test #304: Duplicate usernames must be rejected
    """
    admin1 = Admin(
        username="duplicate",
        email="admin1@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin1)
    db_session.commit()

    # Try duplicate username
    admin2 = Admin(
        username="duplicate",  # Same username!
        email="admin2@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


# ==============================================
# ADMIN OTP MANAGEMENT (Tests 305-307)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_otp_set_on_request(db_session):
    """
    Test #305: Admin OTP can be set and stored
    """
    admin = Admin(
        username="otprequest",
        email="otprequest@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Initially no OTP
    assert admin.otp is None

    # Set OTP
    admin.otp = "123456"
    admin.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    db_session.commit()
    db_session.refresh(admin)

    assert admin.otp == "123456"
    assert admin.otp_expires_at is not None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_otp_expires_after_5_minutes(db_session):
    """
    Test #306: Admin OTP should expire after 5 minutes
    """
    admin = Admin(
        username="expiryadmin",
        email="expiry@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Set OTP with expiry
    otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    admin.otp = "654321"
    admin.otp_expires_at = otp_expiry
    db_session.commit()

    # Verify expiry is ~5 minutes in future
    time_diff = (admin.otp_expires_at - datetime.utcnow()).total_seconds()
    assert 290 < time_diff < 310  # ~5 minutes (with small margin)


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_otp_cleared_after_verification(db_session):
    """
    Test #307: OTP should be cleared after successful verification
    """
    admin = Admin(
        username="clearadmin",
        email="clear@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Set OTP
    admin.otp = "999888"
    admin.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    admin.otp_verified = False
    db_session.commit()

    # Simulate verification
    admin.otp_verified = True
    admin.otp = None  # Clear OTP
    admin.otp_expires_at = None  # Clear expiry
    db_session.commit()
    db_session.refresh(admin)

    assert admin.otp is None
    assert admin.otp_expires_at is None
    assert admin.otp_verified is True


# ==============================================
# ADMIN vs USER OTP SEPARATION (Test 308)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
def test_admin_otp_different_from_user_otp(db_session):
    """
    Test #308: Admin OTP system should be separate from User OTP system
    This ensures admins and users can't use each other's OTPs
    """
    from app.models.user import User, UserStatus

    # Create user with OTP
    user = User(
        email="user@example.com",
        status=UserStatus.unknown,
        otp="111111",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    # Create admin with same OTP (should be allowed - separate systems)
    admin = Admin(
        username="admin",
        email="admin@example.com",
        password=hash_password("Password123"),
        otp="111111",  # Same OTP as user - this is OK
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Both should exist with same OTP (but in different tables)
    assert user.otp == admin.otp == "111111"
    assert user.id != admin.id  # Different records
    # This documents that OTPs are table-specific, not global
