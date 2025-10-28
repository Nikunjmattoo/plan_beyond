# PostgreSQL Test Database Setup

## Overview

The test suite requires a **PostgreSQL test database** to run integration tests. This ensures tests match production behavior exactly.

**Why PostgreSQL (not SQLite)?**
- ✓ Exact production environment match
- ✓ Tests real PostgreSQL constraints (ENUM, CHECK, etc.)
- ✓ Catches PostgreSQL-specific bugs
- ✓ Validates case-sensitivity handling
- ✓ Tests JSONB behavior

## Quick Setup (Windows)

### Option 1: Automated Setup (Recommended)

**Run the batch script:**
```cmd
setup_test_db.bat
```

This will:
1. Create test user: `test` / `test`
2. Grant CREATEDB privilege
3. Create database: `test_plan_beyond`
4. Configure permissions

### Option 2: Manual Setup

**Run SQL script:**
```cmd
psql -U postgres -f setup_test_db.sql
```

**Or using pgAdmin:**
1. Open pgAdmin
2. Connect to PostgreSQL
3. Open Query Tool
4. Copy and run contents of `setup_test_db.sql`

## Test Database Configuration

**Connection Details:**
- **Host:** localhost
- **Port:** 5432
- **Database:** test_plan_beyond
- **User:** test
- **Password:** test

**Connection String:**
```
postgresql://test:test@localhost:5432/test_plan_beyond
```

## How Tests Work

### 1. Test Database Creation (Automatic)

When you run tests, pytest automatically:
1. Creates a **temporary database** with timestamp (e.g., `test_plan_beyond_1704067200`)
2. Applies full schema from SQLAlchemy models
3. Runs all tests
4. **Drops the temporary database** when done

This means:
- ✓ No manual cleanup needed
- ✓ Each test session is isolated
- ✓ No data pollution between runs

### 2. Test Isolation (Transaction Rollback)

Each test runs in its own transaction:
```python
@pytest.fixture(scope="function")
def db_session(test_db_engine):
    session = SessionLocal()
    yield session
    session.rollback()  # Automatic rollback
    session.close()
```

This means:
- ✓ Tests don't affect each other
- ✓ Database is clean for every test
- ✓ Failed tests don't leave dirty data

### 3. Test Fixtures

**Available fixtures:**
- `db_session` - Database session with auto-rollback
- `test_user` - Pre-created verified user
- `test_admin` - Pre-created admin user
- `test_contact` - Pre-created contact
- `multiple_users` - 5 test users
- `multiple_contacts` - 5 test contacts

**Example test:**
```python
def test_create_user(db_session):
    user = User(email="test@example.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
```

## Running Tests

### Run All Database Model Tests (45 tests)
```bash
pytest tests/unit/foundation/test_database_models.py -v
```

### Run Specific Test
```bash
pytest tests/unit/foundation/test_database_models.py::test_user_email_unique_constraint_enforced -v
```

### Run with Coverage
```bash
pytest tests/unit/foundation/ --cov=models --cov-report=html
```

### Run All Foundation Tests (102 tests)
```bash
pytest tests/unit/foundation/ -v
```

## Test Database Requirements

The `test` user needs these privileges:

1. **CREATEDB** - Create temporary test databases
   ```sql
   ALTER USER test CREATEDB;
   ```

2. **CONNECT** - Connect to test database
   ```sql
   GRANT CONNECT ON DATABASE test_plan_beyond TO test;
   ```

3. **SCHEMA privileges** - Create/modify schema
   ```sql
   GRANT ALL ON SCHEMA public TO test;
   ```

4. **TABLE privileges** - Full table access
   ```sql
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test;
   ```

## Troubleshooting

### Error: "connection refused"
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**Solution:**
1. Make sure PostgreSQL is running
2. Check Windows Services → PostgreSQL is started
3. Verify port 5432 is not blocked

**Check if PostgreSQL is running:**
```cmd
psql -U postgres -c "SELECT version();"
```

### Error: "database does not exist"
```
psycopg2.OperationalError: database "test_plan_beyond" does not exist
```

**Solution:**
Run the setup script again:
```cmd
setup_test_db.bat
```

### Error: "permission denied"
```
psycopg2.OperationalError: permission denied to create database
```

**Solution:**
The `test` user needs CREATEDB privilege:
```sql
ALTER USER test CREATEDB;
```

### Error: "role does not exist"
```
psycopg2.OperationalError: role "test" does not exist
```

**Solution:**
Create the test user:
```sql
CREATE USER test WITH PASSWORD 'test';
ALTER USER test CREATEDB;
```

### Error: Import errors (FastAPI, Slowapi, etc.)
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
Install dependencies:
```cmd
pip install -r requirements.txt
```

## Cleanup

### Remove Test Databases
```sql
-- Connect to postgres database
\c postgres

-- Drop all test databases
DROP DATABASE IF EXISTS test_plan_beyond;

-- Drop timestamped test databases (if any remain)
SELECT 'DROP DATABASE ' || datname || ';'
FROM pg_database
WHERE datname LIKE 'test_%';
```

### Remove Test User
```sql
DROP USER IF EXISTS test;
```

## CI/CD Integration

For CI/CD pipelines, use Docker:

```yaml
# .github/workflows/tests.yml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_plan_beyond
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

## Test Database vs Production Database

**Test Database:**
- Name: `test_plan_beyond` (base) + timestamp
- Auto-created/destroyed
- Empty schema (no seed data)
- Used only for testing

**Production Database:**
- Name: `plan_beyond` (or your production DB name)
- Persistent
- Contains real user data
- Never touched by tests

**Safety:** Tests **never** connect to production database. Connection string is hard-coded in `conftest.py` to use `test_plan_beyond`.

## Next Steps

After setup:

1. ✓ Run database model tests:
   ```bash
   pytest tests/unit/foundation/test_database_models.py -v
   ```

2. ✓ Verify all 45 tests pass

3. ✓ Continue to remaining Module 1 tests:
   - test_database_relationships.py (20 tests)
   - test_config.py (15 tests)
   - test_security_core.py (12 tests)
   - test_dependencies.py (10 tests)

## Questions?

See tests/README.md for complete test suite documentation.
