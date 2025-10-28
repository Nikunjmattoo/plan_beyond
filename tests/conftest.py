"""
Root conftest.py - Shared fixtures for all tests
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set test environment before any app imports
os.environ["TESTING"] = "1"

from app.main import app
from app.dependencies import get_db

# Import all fixture modules to make them available
pytest_plugins = [
    "tests.fixtures.database_fixtures",
    "tests.fixtures.user_fixtures",
    "tests.fixtures.auth_fixtures",
]


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """
    Create a FastAPI test client with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


# ==============================================
# AUTHENTICATION FIXTURES
# ==============================================

@pytest.fixture
def auth_headers(test_user, test_user_token):
    """
    Return authorization headers with valid JWT token.
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_admin, test_admin_token):
    """
    Return authorization headers with valid admin JWT token.
    """
    return {"Authorization": f"Bearer {test_admin_token}"}


# ==============================================
# CLEANUP FIXTURES
# ==============================================

@pytest.fixture(autouse=True)
def reset_state():
    """
    Automatically reset any global state before each test.
    """
    # Reset any caches, singletons, or global state here
    yield
    # Cleanup after test


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """
    Set up test environment variables.
    """
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    monkeypatch.setenv("S3_PUBLIC_BASE_URL", "https://test-bucket.s3.amazonaws.com")
    monkeypatch.setenv("KMS_KEY_ID", "test-kms-key-id")
    monkeypatch.setenv("SMTP_EMAIL", "test@example.com")
    monkeypatch.setenv("SMTP_APP_PASSWORD", "test-password")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "test-credentials.json")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "test-twilio-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-twilio-token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+1234567890")


# ==============================================
# PYTEST HOOKS
# ==============================================

def pytest_configure(config):
    """
    Custom pytest configuration.
    """
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test location.
    """
    for item in items:
        # Auto-mark tests based on directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark slow tests
        if "performance" in str(item.fspath) or "concurrency" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


# ==============================================
# TEST RESULT TRACKING
# ==============================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Track test results for custom reporting.
    """
    outcome = yield
    report = outcome.get_result()

    # Store test result in item for access in fixtures
    setattr(item, f"report_{report.when}", report)
