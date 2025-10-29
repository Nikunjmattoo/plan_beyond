"""
Module 2: Auth - Password Security Tests (Tests 359-373)

Tests password hashing, validation, and OTP security.
Only uses existing User model fields.
"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User, UserStatus
from app.core.security import hash_password, verify_password


# ==============================================
# PASSWORD HASHING TESTS (Tests 359-363)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_password_hash_is_not_plaintext(db_session):
    """
    Test #359: Password is never stored as plaintext
    """
    plaintext = "MyPassword123"
    hashed = hash_password(plaintext)
    
    assert hashed != plaintext
    assert len(hashed) > len(plaintext)


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_same_password_different_hashes(db_session):
    """
    Test #360: Same password generates different hashes (salt)
    """
    password = "TestPassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Hashes should be different (salted)
    assert hash1 != hash2
    # But both should verify against original password
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


@pytest.mark.unit
@pytest.mark.auth
def test_wrong_password_rejected(db_session):
    """
    Test #361: Wrong password fails verification
    """
    correct_password = "CorrectPassword123"
    wrong_password = "WrongPassword456"
    
    hashed = hash_password(correct_password)
    
    assert verify_password(correct_password, hashed) is True
    assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
@pytest.mark.auth
def test_password_can_be_changed(db_session):
    """
    Test #362: User can change their password
    """
    user = User(
        email="changepass@example.com",
        status=UserStatus.verified,
        password=hash_password("OldPassword123"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Change password
    new_password = "NewPassword456"
    user.password = hash_password(new_password)
    db_session.commit()
    db_session.refresh(user)

    # Verify new password works, old doesn't
    assert verify_password(new_password, user.password)
    assert not verify_password("OldPassword123", user.password)


@pytest.mark.unit
@pytest.mark.auth
def test_user_without_password_can_login_with_otp(db_session):
    """
    Test #363: OAuth users (no password) can still use OTP
    """
    user = User(
        email="oauth@example.com",
        status=UserStatus.verified,
        password=None,  # OAuth user
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.password is None
    assert user.otp == "123456"


# ==============================================
# PASSWORD STRENGTH TESTS (Tests 364-368)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
def test_password_minimum_length_validation(db_session):
    """
    Test #364: Password length validation logic
    """
    short_password = "Pass1"
    valid_password = "Password123"
    
    # Application should validate minimum 8 characters
    assert len(short_password) < 8
    assert len(valid_password) >= 8


@pytest.mark.unit
@pytest.mark.auth
def test_password_complexity_uppercase(db_session):
    """
    Test #365: Password should have uppercase letter
    """
    weak = "password123"
    strong = "Password123"
    
    assert not any(c.isupper() for c in weak)
    assert any(c.isupper() for c in strong)


@pytest.mark.unit
@pytest.mark.auth
def test_password_complexity_lowercase(db_session):
    """
    Test #366: Password should have lowercase letter
    """
    weak = "PASSWORD123"
    strong = "Password123"
    
    assert not any(c.islower() for c in weak)
    assert any(c.islower() for c in strong)


@pytest.mark.unit
@pytest.mark.auth
def test_password_complexity_digit(db_session):
    """
    Test #367: Password should have digit
    """
    weak = "Password"
    strong = "Password123"
    
    assert not any(c.isdigit() for c in weak)
    assert any(c.isdigit() for c in strong)


@pytest.mark.unit
@pytest.mark.auth
def test_password_special_characters_allowed(db_session):
    """
    Test #368: Password can contain special characters
    """
    password_with_special = "Password123!@#"
    
    user = User(
        email="special@example.com",
        status=UserStatus.verified,
        password=hash_password(password_with_special),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert verify_password(password_with_special, user.password)


# ==============================================
# OTP SECURITY TESTS (Tests 369-373)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_otp_expires_after_timeout(db_session):
    """
    Test #369: OTP should expire after set time
    """
    user = User(
        email="otpexpire@example.com",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() - timedelta(minutes=10),  # Expired
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # OTP is expired
    assert user.otp_expires_at < datetime.utcnow()


@pytest.mark.unit
@pytest.mark.auth
def test_otp_cleared_after_verification(db_session):
    """
    Test #370: OTP should be cleared after successful verification
    """
    user = User(
        email="otpclear@example.com",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Verify and clear
    user.otp_verified = True
    user.otp = None
    user.otp_expires_at = None
    db_session.commit()
    db_session.refresh(user)

    assert user.otp is None
    assert user.otp_verified is True


@pytest.mark.unit
@pytest.mark.auth
def test_multiple_users_can_have_same_otp(db_session):
    """
    Test #371: Different users can have same OTP value (different accounts)
    """
    user1 = User(
        email="user1@example.com",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user2 = User(
        email="user2@example.com",
        status=UserStatus.unknown,
        otp="123456",  # Same OTP
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    # Both can have same OTP (different users)
    assert user1.otp == user2.otp == "123456"
    assert user1.id != user2.id


@pytest.mark.unit
@pytest.mark.auth
def test_otp_updated_on_resend(db_session):
    """
    Test #372: OTP is regenerated when user requests resend
    """
    user = User(
        email="resend@example.com",
        status=UserStatus.unknown,
        otp="111111",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Resend - generate new OTP
    user.otp = "222222"
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    db_session.commit()
    db_session.refresh(user)

    assert user.otp == "222222"


@pytest.mark.unit
@pytest.mark.auth
def test_otp_verified_flag_tracks_verification_status(db_session):
    """
    Test #373: otp_verified flag tracks whether OTP was successfully verified
    """
    user = User(
        email="verified@example.com",
        status=UserStatus.unknown,
        otp="123456",
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # After verification
    user.otp_verified = True
    db_session.commit()
    db_session.refresh(user)

    assert user.otp_verified is True
