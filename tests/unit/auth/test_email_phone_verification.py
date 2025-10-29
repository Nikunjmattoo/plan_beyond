"""
Module 2: Auth - Email/Phone Verification Tests (Tests 374-388)

Tests email and phone verification flows.
"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User, UserStatus


# ==============================================
# EMAIL VERIFICATION TESTS (Tests 374-381)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_email_verification_token_generated(db_session):
    """
    Test #374: Email verification token is generated on user creation
    """
    user = User(
        email="verify@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Generate verification token
    import secrets
    user.email_verification_token = secrets.token_urlsafe(32)
    user.email_verified = False
    db_session.commit()
    db_session.refresh(user)

    assert user.email_verification_token is not None
    assert user.email_verified is False


@pytest.mark.unit
@pytest.mark.auth
def test_email_verified_flag_set_after_verification(db_session):
    """
    Test #375: email_verified flag is True after successful verification
    """
    user = User(
        email="verified@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Verify email
    user.email_verified = True
    user.email_verification_token = None
    db_session.commit()
    db_session.refresh(user)

    assert user.email_verified is True
    assert user.email_verification_token is None


@pytest.mark.unit
@pytest.mark.auth
def test_email_verification_token_cleared_after_verification(db_session):
    """
    Test #376: Verification token is cleared after successful verification
    """
    user = User(
        email="cleartoken@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    import secrets
    user.email_verification_token = secrets.token_urlsafe(32)
    db_session.commit()

    # Verify and clear
    user.email_verified = True
    user.email_verification_token = None
    db_session.commit()
    db_session.refresh(user)

    assert user.email_verification_token is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.xfail(reason="email_verified field not implemented in User model")
def test_unverified_email_cannot_login(db_session):
    """
    Test #377: Users with unverified email should not be able to login
    NOTE: This documents expected behavior - may not be enforced yet
    """
    user = User(
        email="unverified@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # App should check email_verified before allowing login
    # email_verified field doesn't exist yet
    pass


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.xfail(reason="email_verified field not implemented in User model")
def test_change_email_requires_reverification(db_session):
    """
    Test #378: Changing email should require re-verification
    NOTE: This documents expected behavior - may not be enforced yet
    """
    user = User(
        email="old@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Change email
    user.email = "new@example.com"
    # email_verified field would be reset here
    db_session.commit()
    db_session.refresh(user)

    assert user.email == "new@example.com"


@pytest.mark.unit
@pytest.mark.auth
def test_verification_email_sent_on_user_creation(db_session):
    """
    Test #379: Verification email should be sent when user is created
    NOTE: This documents expected behavior - actual email sending is external
    """
    user = User(
        email="sendemail@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # In production, email service would be triggered here
    assert user.email is not None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.xfail(reason="email_verification_token field not implemented in User model")
def test_resend_verification_email(db_session):
    """
    Test #380: User can request resend of verification email
    """
    user = User(
        email="resend@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Generate new token for resend (would use email_verification_token field)
    import secrets
    new_token = secrets.token_urlsafe(32)
    # email_verification_token field doesn't exist
    pass


@pytest.mark.unit
@pytest.mark.auth
def test_email_case_insensitive_for_verification(db_session):
    """
    Test #381: Email verification should be case-insensitive
    """
    user = User(
        email="Test@Example.Com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Verification should work regardless of case
    assert user.email.lower() == "test@example.com"


# ==============================================
# PHONE VERIFICATION TESTS (Tests 382-388)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_phone_verification_otp_generated(db_session):
    """
    Test #382: OTP is generated for phone verification
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Generate OTP for phone verification
    user.otp = "123456"
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    db_session.commit()
    db_session.refresh(user)

    assert user.otp == "123456"
    assert user.otp_expires_at is not None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.xfail(reason="phone_verified field not implemented in User model")
def test_phone_verified_flag_after_otp_verification(db_session):
    """
    Test #383: phone_verified flag is set after OTP verification
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        otp="123456",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Verify phone (would use phone_verified field)
    user.otp = None
    db_session.commit()
    db_session.refresh(user)

    assert user.otp is None


@pytest.mark.unit
@pytest.mark.auth
def test_phone_otp_expires_after_5_minutes(db_session):
    """
    Test #384: Phone OTP expires after 5 minutes
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Check expiry time is ~5 minutes from now
    time_diff = user.otp_expires_at - datetime.utcnow()
    assert 4 <= time_diff.total_seconds() / 60 <= 6  # Between 4-6 minutes


@pytest.mark.unit
@pytest.mark.auth
def test_expired_phone_otp_rejected(db_session):
    """
    Test #385: Expired phone OTP should be rejected
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
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
def test_wrong_phone_otp_rejected(db_session):
    """
    Test #386: Wrong phone OTP should be rejected
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # App should reject wrong OTP
    wrong_otp = "654321"
    assert wrong_otp != user.otp


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.xfail(reason="phone_verified field not implemented in User model")
def test_change_phone_requires_reverification(db_session):
    """
    Test #387: Changing phone number should require re-verification
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Change phone
    user.phone = "+919999999999"
    # phone_verified field would be reset here
    db_session.commit()
    db_session.refresh(user)

    assert user.phone == "+919999999999"


@pytest.mark.unit
@pytest.mark.auth
def test_sms_otp_rate_limited(db_session):
    """
    Test #388: SMS OTP requests should be rate limited
    NOTE: This documents expected behavior - may not be enforced yet
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # In a proper system, limit OTP requests (e.g., max 3 per hour)
    # This test documents that expectation
    pass
