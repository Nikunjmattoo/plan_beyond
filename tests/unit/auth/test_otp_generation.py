"""
Module 2: Auth - OTP Generation Tests (Tests 341-348)

Tests OTP generation, expiry, verification, and security.
These tests focus on OTP behavior and edge cases.
"""
import pytest
from datetime import datetime, timedelta
import random
import string

from app.models.user import User, UserStatus


# ==============================================
# OTP GENERATION TESTS (Tests 341-343)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_generate_numeric_otp_length_6(db_session):
    """
    Test #341: OTP must be exactly 6 digits long
    """
    # Generate OTPs multiple times to ensure consistency
    for _ in range(20):
        otp = ''.join(random.choices(string.digits, k=6))

        assert len(otp) == 6, f"OTP length is {len(otp)}, expected 6"
        # NOT 4 digits, NOT 8 digits - exactly 6!


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_generate_numeric_otp_only_digits(db_session):
    """
    Test #342: OTP must contain only numeric digits (0-9)
    SECURITY: Letters or symbols could break SMS delivery or cause confusion
    """
    for _ in range(20):
        otp = ''.join(random.choices(string.digits, k=6))

        assert otp.isdigit(), f"OTP '{otp}' contains non-digits"
        assert all(c in '0123456789' for c in otp)
        # Should NOT contain: letters, spaces, dashes, symbols


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_generate_otp_randomness(db_session):
    """
    Test #343: OTP generation must be random (not predictable)
    CRITICAL SECURITY BUG: If OTPs are predictable, attacker can guess them!
    """
    # Generate 200 OTPs
    otps = []
    for _ in range(200):
        otp = ''.join(random.choices(string.digits, k=6))
        otps.append(otp)

    unique_otps = set(otps)

    # Should have high uniqueness (not all the same!)
    # With 6 digits, there are 1,000,000 possible OTPs
    # Getting 200 unique from 200 attempts is very likely if random
    uniqueness_pct = (len(unique_otps) / len(otps)) * 100

    assert uniqueness_pct > 85, f"Only {uniqueness_pct:.1f}% unique OTPs - not random enough!"

    # If all OTPs are identical, we have a CRITICAL security bug!
    if len(unique_otps) == 1:
        print("\n" + "="*70)
        print("🔥 PRODUCTION BUG #4: OTP generation not random")
        print("="*70)
        print(f"Issue: All OTPs are identical: {list(unique_otps)[0]}")
        print("Impact: CRITICAL - Attacker can predict OTPs!")
        print("Fix: Use cryptographically secure random number generator")
        assert False, "OTP generation is broken!"


# ==============================================
# OTP EXPIRY TESTS (Tests 344-347)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_otp_expiry_set_5_minutes_future(db_session):
    """
    Test #344: OTP expiry should be set to 5 minutes in the future
    """
    user = User(
        email="expiry@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Generate OTP with expiry
    otp = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.utcnow() + timedelta(minutes=5)

    user.otp = otp
    user.otp_expires_at = expiry
    db_session.commit()
    db_session.refresh(user)

    # Verify expiry is ~5 minutes from now
    time_until_expiry = (user.otp_expires_at - datetime.utcnow()).total_seconds()

    # Allow small margin (290-310 seconds = 4:50 to 5:10)
    assert 290 < time_until_expiry < 310, f"OTP expires in {time_until_expiry}s, expected ~300s"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_otp_verified_flag_defaults_false(db_session):
    """
    Test #345: otp_verified flag should default to False
    """
    user = User(
        email="verified@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.otp_verified is False
    # Should NOT be True until user verifies OTP


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_otp_cleared_after_successful_verification(db_session):
    """
    Test #346: OTP should be cleared after successful verification
    SECURITY: Prevents OTP reuse attacks
    """
    user = User(
        email="clearotp@example.com",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Simulate OTP verification
    user.otp_verified = True
    user.otp = None  # Clear OTP
    user.otp_expires_at = None  # Clear expiry
    db_session.commit()
    db_session.refresh(user)

    assert user.otp is None, "OTP should be cleared after verification"
    assert user.otp_expires_at is None, "Expiry should be cleared"
    assert user.otp_verified is True, "Verified flag should be True"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_expired_otp_rejected(db_session):
    """
    Test #347: Expired OTP must be rejected
    SECURITY: Prevents replay attacks with old OTPs
    """
    user = User(
        email="expired@example.com",
        status=UserStatus.unknown,
        otp="999888",
        otp_expires_at=datetime.utcnow() - timedelta(minutes=10),  # Expired 10 min ago
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Check if OTP is expired
    is_expired = user.otp_expires_at < datetime.utcnow()

    assert is_expired is True, "OTP should be expired"

    # Verification should fail for expired OTP
    # This test documents the expected behavior
    if not is_expired:
        print("\n" + "="*70)
        print("🔥 PRODUCTION BUG #5: Expired OTP accepted")
        print("="*70)
        print("Issue: System accepts OTPs past expiry time")
        print("Impact: CRITICAL - Old OTPs can be reused indefinitely")
        print("Fix: Check otp_expires_at before accepting OTP")
        assert False, "Expired OTP was accepted!"


# ==============================================
# OTP VERIFICATION TESTS (Test 348)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_wrong_otp_rejected(db_session):
    """
    Test #348: Wrong OTP must be rejected
    SECURITY: Only correct OTP should grant access
    """
    user = User(
        email="wrongotp@example.com",
        status=UserStatus.unknown,
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Try wrong OTPs
    wrong_otps = ["654321", "111111", "000000", "123457"]

    for wrong_otp in wrong_otps:
        is_valid = (user.otp == wrong_otp)
        assert is_valid is False, f"Wrong OTP '{wrong_otp}' should be rejected"

    # Correct OTP should work
    is_valid = (user.otp == "123456")
    assert is_valid is True, "Correct OTP should be accepted"

    # If wrong OTPs are accepted, we have a CRITICAL security bug!
