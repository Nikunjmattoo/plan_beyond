"""
Root conftest.py - Shared fixtures for all tests
"""
import os
import sys
import pytest

# Add parent directory to Python path
# This makes /home/user/plan_beyond importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Create 'app' module alias by adding current directory as 'app' in sys.modules
# This allows code to use 'from app.* import' even though directory is 'plan_beyond'
import types
app_module_alias = types.ModuleType('app')
sys.modules['app'] = app_module_alias
app_module_alias.__path__ = [project_root]
app_module_alias.__file__ = os.path.join(project_root, '__init__.py')

# Set test environment variables BEFORE importing app (to avoid Settings validation errors)
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars-long"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "43200"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AWS_ACCESS_KEY_ID"] = "test-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret-key"
os.environ["AWS_REGION"] = "ap-south-1"
os.environ["S3_BUCKET"] = "test-bucket"
os.environ["S3_PUBLIC_BASE_URL"] = "https://test-bucket.s3.amazonaws.com"
os.environ["KMS_KEY_ID"] = "test-kms-key-id"
os.environ["SMTP_EMAIL"] = "test@example.com"
os.environ["SMTP_APP_PASSWORD"] = "test-password"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "test-credentials.json"
os.environ["TWILIO_ACCOUNT_SID"] = "test-twilio-sid"
os.environ["TWILIO_AUTH_TOKEN"] = "test-twilio-token"
os.environ["TWILIO_PHONE_NUMBER"] = "+1234567890"

# Detect if running ORM tests - they're in tests/unit/models/ and don't need full app
_running_orm_tests = any('tests/unit/models' in arg or 'tests\\unit\\models' in arg for arg in sys.argv)

# Detect if running foundation tests - they need database fixtures but not full app
_running_foundation_tests = any('tests/unit/foundation' in arg or 'tests\\unit\\foundation' in arg for arg in sys.argv)

# Detect if running auth tests - they need database fixtures but not full app
_running_auth_tests = any('tests/unit/auth' in arg or 'tests\\unit\\auth' in arg for arg in sys.argv)

# Configure loading based on test type
if _running_orm_tests:
    # ORM tests: No app, no fixtures (they have their own minimal conftest)
    TestClient = None
    app = None
    get_db = None
    pytest_plugins = []
elif _running_foundation_tests or _running_auth_tests:
    # Foundation/Auth tests: No app, but NEED database fixtures
    TestClient = None
    app = None
    get_db = None
    pytest_plugins = [
        "tests.fixtures.database_fixtures",
        "tests.fixtures.user_fixtures",
    ]
else:
    # All other tests: Load everything
    from fastapi.testclient import TestClient
    from app.main import app
    from app.dependencies import get_db

    pytest_plugins = [
        "tests.fixtures.database_fixtures",
        "tests.fixtures.user_fixtures",
        "tests.fixtures.auth_fixtures",
    ]


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a FastAPI test client with overridden database dependency.
    """
    if app is None:
        pytest.skip("FastAPI app not loaded for ORM tests")

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
