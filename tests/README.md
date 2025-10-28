# Plan Beyond - Test Suite Documentation

## Overview

This directory contains the comprehensive test suite for the Plan Beyond estate planning and legacy management platform.

**Total Tests:** 1,644 tests across 129 test files
**Current Status:** 156/1,644 tests (9.5% complete)

## Directory Structure

```
tests/
├── conftest.py                    # Root fixtures (DB, client, auth)
├── pytest.ini                     # Pytest configuration
├── run_all_tests.py              # Test runner script with progress bars
├── README.md                     # This file
│
├── fixtures/                     # Reusable test fixtures
│   ├── database_fixtures.py      # DB session, cleanup fixtures
│   ├── user_fixtures.py          # User, admin, contact fixtures
│   ├── auth_fixtures.py          # Tokens, OTP fixtures
│   ├── vault_fixtures.py         # Encrypted file fixtures
│   ├── mock_fixtures.py          # Mock AWS, SMTP, Twilio
│   └── factory_fixtures.py       # Factory Boy factories
│
├── unit/                         # UNIT TESTS (1,145 tests)
│   ├── models/                   # ✓ Module 0: ORM Models (156 tests) - COMPLETE
│   ├── foundation/               # Module 1: Foundation Layer (102 tests)
│   ├── auth/                     # Module 2: Authentication (85 tests)
│   ├── vault/                    # Module 3: Vault & Encryption (125 tests)
│   ├── categories/               # Module 4: Digital Asset Organization (107 tests)
│   ├── folders/                  # Module 5: Folder & Relationship System (77 tests)
│   ├── memories/                 # Module 6: Memory & Message Collections (73 tests)
│   ├── death/                    # Module 7: Death Declaration System (129 tests)
│   ├── reminders/                # Module 8: Reminder System (82 tests)
│   ├── policy_checker/           # Module 9: Policy Checker & OCR (68 tests)
│   ├── file_storage/             # Module 10: File & Storage Services (52 tests)
│   ├── admin/                    # Module 11: Admin Operations (47 tests)
│   └── external_services/        # Module 12: Integration & External Services (42 tests)
│
├── integration/                  # INTEGRATION TESTS (290 tests)
│   ├── foundation/               # Database transactions
│   ├── auth/                     # Auth & User API endpoints
│   ├── vault/                    # Vault API endpoints & encryption flow
│   ├── categories/               # Category API endpoints
│   ├── folders/                  # Folder API endpoints
│   ├── memories/                 # Memory API endpoints
│   ├── death/                    # Death declaration API endpoints
│   ├── reminders/                # Reminder API endpoints
│   ├── policy_checker/           # Policy checker API endpoints
│   └── file_storage/             # S3 upload API endpoints
│
└── e2e/                          # END-TO-END TESTS (91 tests)
    ├── user_journeys/            # Complete user workflows
    ├── workflows/                # Complex multi-step scenarios
    ├── security/                 # Security testing
    ├── performance/              # Performance benchmarks
    └── regression/               # Regression tests
```

## Test Categories

### Unit Tests (1,145 tests - 69.6%)
- Test individual functions and classes in isolation
- Mock external dependencies (database, S3, email services)
- Fast execution (< 1 second per test)
- No external service calls

### Integration Tests (290 tests - 17.6%)
- Test API endpoints with real database
- Test service interactions
- Validate request/response flows
- Use test database with transaction rollback

### End-to-End Tests (91 tests - 5.5%)
- Test complete user journeys
- Simulate real user behavior
- Test cross-module functionality
- Full stack testing (API + DB + External services mocked)

### Specialized Tests (118 tests - 7.2%)
- Security tests (authentication, authorization, encryption)
- Performance tests (load testing, response times)
- Concurrency tests (race conditions, deadlocks)
- Regression tests (bug fixes validation)

## Running Tests

### Run All ORM Tests (Module 0)
```bash
# From project root
python tests/run_all_tests.py

# Or using pytest directly
pytest tests/unit/models/ -v
```

### Run Specific Test Module
```bash
pytest tests/unit/models/test_user_model.py -v
```

### Run Tests by Marker
```bash
# Run only ORM tests
pytest -m orm -v

# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v
```

### Run with Coverage
```bash
pytest tests/unit/models/ --cov=models --cov-report=html
```

## Test Progress

### ✓ Completed Modules

**Module 0: ORM Models (156/156 tests - 100%)**
- ✓ User Model (15 tests)
- ✓ Contact Model (12 tests)
- ✓ Vault File Model (15 tests)
- ✓ Folder Model (12 tests)
- ✓ Memory Collection Model (12 tests)
- ✓ Death Declaration Model (15 tests)
- ✓ Trustee Model (10 tests)
- ✓ Category Model (10 tests)
- ✓ Section Model (10 tests)
- ✓ Step Model (12 tests)
- ✓ Reminder Model (10 tests)
- ✓ Admin Model (8 tests)
- ✓ Relationship Models (15 tests)

**Coverage:** 99% (872 statements, 4 missed in user.py property methods)

### Pending Modules

**Module 1: Foundation Layer (0/102 tests)**
- Database models validation
- Configuration management
- Security core
- Dependencies

**Module 2-12:** See TEST_PLAN.md for complete breakdown

## Test Fixtures

### Database Fixtures (`database_fixtures.py`)
- `db_session`: Test database session with transaction rollback
- `test_db`: In-memory SQLite database for tests
- Database cleanup and reset utilities

### User Fixtures (`user_fixtures.py`)
- `test_user`: Standard test user
- `test_admin`: Admin user with privileges
- `verified_user`: User with verified email/phone
- `test_contact`: Test contact record

### Auth Fixtures (`auth_fixtures.py`)
- `auth_token`: Valid JWT token
- `expired_token`: Expired JWT token
- `test_otp`: Test OTP code
- `mock_jwt`: Mock JWT utilities

### Vault Fixtures (`vault_fixtures.py`)
- `test_file`: Test file for encryption
- `encrypted_file`: Encrypted test file
- `mock_s3`: Mock S3 client

### Mock Fixtures (`mock_fixtures.py`)
- `mock_twilio`: Mock Twilio SMS service
- `mock_smtp`: Mock email service
- `mock_aws_kms`: Mock AWS KMS service

## Writing New Tests

### Test File Naming Convention
- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_api_endpoints.py`
- E2E tests: `test_<user_journey>_journey.py`

### Test Function Naming
```python
def test_<feature>_<scenario>_<expected_result>():
    """Test description"""
    # Arrange
    # Act
    # Assert
```

### Example Test
```python
import pytest
from models.user import User

@pytest.mark.unit
@pytest.mark.orm
def test_user_model_has_email_column():
    """Test that User model has an email column"""
    from sqlalchemy import inspect

    inspector = inspect(User)
    columns = [col.name for col in inspector.columns]

    assert 'email' in columns
```

## Test Markers

Configure in `pytest.ini`:
- `@pytest.mark.orm`: ORM model schema tests
- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (slower, may hit external services)
- `@pytest.mark.e2e`: End-to-end tests (full stack)
- `@pytest.mark.security`: Security-focused tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Tests that take > 1 second

## Coverage Goals

- **Unit Tests:** 95%+ code coverage
- **Integration Tests:** 85%+ API endpoint coverage
- **E2E Tests:** 100% critical user journeys covered

## CI/CD Integration

Tests run automatically on:
- Pull request creation
- Push to main branch
- Nightly scheduled runs

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`, ensure you're running from project root:
```bash
cd /path/to/plan_beyond
pytest tests/unit/models/ -v
```

### Database Errors
If tests fail with database errors, ensure PostgreSQL is running and environment variables are set:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/test_db"
```

### ORM Tests Not Loading Full App
ORM tests auto-detect and skip loading FastAPI app. This is intentional to avoid dependency issues during schema validation.

## Contact

For questions or issues with the test suite, contact the development team or create a GitHub issue.

---

**Last Updated:** October 28, 2025
**Test Suite Version:** 1.0.0
**Progress:** 156/1,644 tests (9.5% complete)
