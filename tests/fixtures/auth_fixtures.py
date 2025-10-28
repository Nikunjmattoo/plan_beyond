"""
Authentication fixtures for JWT tokens, OTP, and sessions.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.config import settings


# ==============================================
# JWT TOKEN FIXTURES
# ==============================================

@pytest.fixture
def test_user_token(test_user) -> str:
    """
    Generate a valid JWT token for the test user.
    """
    payload = {
        "sub": str(test_user.id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def test_admin_token(test_admin) -> str:
    """
    Generate a valid JWT token for the test admin.
    """
    payload = {
        "sub": str(test_admin.id),
        "adm": True,  # Admin flag
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def expired_token(test_user) -> str:
    """
    Generate an expired JWT token.
    """
    payload = {
        "sub": str(test_user.id),
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        "iat": datetime.utcnow() - timedelta(hours=2),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def invalid_token() -> str:
    """
    Generate a token with invalid signature.
    """
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    # Use wrong secret key
    token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
    return token


@pytest.fixture
def token_missing_claims() -> str:
    """
    Generate a token missing required claims.
    """
    payload = {
        "exp": datetime.utcnow() + timedelta(hours=1),
        # Missing "sub" claim
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def second_user_token(second_test_user) -> str:
    """
    Generate a valid JWT token for the second test user.
    """
    payload = {
        "sub": str(second_test_user.id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


# ==============================================
# OTP FIXTURES
# ==============================================

@pytest.fixture
def valid_otp() -> str:
    """
    Generate a valid 6-digit OTP.
    """
    return "123456"


@pytest.fixture
def expired_otp_timestamp():
    """
    Return an expired OTP timestamp (5 minutes ago).
    """
    return datetime.utcnow() - timedelta(minutes=6)


@pytest.fixture
def valid_otp_timestamp():
    """
    Return a valid OTP timestamp (1 minute ago, still valid).
    """
    return datetime.utcnow() - timedelta(minutes=1)


@pytest.fixture
def test_user_with_otp(db_session, test_user):
    """
    Test user with a valid OTP set.
    """
    test_user.otp = "123456"
    test_user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    test_user.otp_verified = False
    db_session.commit()
    db_session.refresh(test_user)
    return test_user


@pytest.fixture
def test_user_with_expired_otp(db_session, test_user):
    """
    Test user with an expired OTP.
    """
    test_user.otp = "123456"
    test_user.otp_expires_at = datetime.utcnow() - timedelta(minutes=6)
    test_user.otp_verified = False
    db_session.commit()
    db_session.refresh(test_user)
    return test_user


# ==============================================
# AUTH HEADER FIXTURES
# ==============================================

@pytest.fixture
def auth_headers(test_user_token) -> dict:
    """
    Return authorization headers with valid JWT token.
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_admin_token) -> dict:
    """
    Return authorization headers with valid admin JWT token.
    """
    return {"Authorization": f"Bearer {test_admin_token}"}


@pytest.fixture
def second_user_auth_headers(second_user_token) -> dict:
    """
    Return authorization headers for the second user.
    """
    return {"Authorization": f"Bearer {second_user_token}"}


@pytest.fixture
def expired_auth_headers(expired_token) -> dict:
    """
    Return authorization headers with expired token.
    """
    return {"Authorization": f"Bearer {expired_token}"}


@pytest.fixture
def invalid_auth_headers(invalid_token) -> dict:
    """
    Return authorization headers with invalid token.
    """
    return {"Authorization": f"Bearer {invalid_token}"}


@pytest.fixture
def no_auth_headers() -> dict:
    """
    Return empty headers (no authentication).
    """
    return {}


__all__ = [
    "test_user_token",
    "test_admin_token",
    "expired_token",
    "invalid_token",
    "token_missing_claims",
    "second_user_token",
    "valid_otp",
    "expired_otp_timestamp",
    "valid_otp_timestamp",
    "test_user_with_otp",
    "test_user_with_expired_otp",
    "auth_headers",
    "admin_auth_headers",
    "second_user_auth_headers",
    "expired_auth_headers",
    "invalid_auth_headers",
    "no_auth_headers",
]
