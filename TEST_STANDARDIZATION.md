# TEST STANDARDIZATION ANALYSIS

## Current Inconsistencies

### Module 0: ORM Tests (156 tests)
**Location:** `tests/unit/models/`

**Current Pattern:**
```python
"""
ORM Tests for User Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.user import User

@pytest.mark.unit
@pytest.mark.orm
def test_user_model_table_name():
    """Test 1: Verify User model table name is 'users'"""
    assert User.__tablename__ == "users"
```

**Issues:**
- ❌ Docstring uses "Test 1" (no # symbol)
- ❌ No `@pytest.mark.critical` marker
- ❌ No section comments (no visual grouping)
- ❌ No fixture usage (but doesn't need it for schema tests)

### Module 1: Foundation Tests (45 tests)
**Location:** `tests/unit/foundation/`

**Current Pattern:**
```python
"""
Module 1: Foundation - Database Models Tests (Tests 1-15)

Tests basic model creation, relationships, and constraints.
"""
import pytest
from datetime import datetime

from app.models.user import User
from tests.helpers.bug_reporter import report_production_bug

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
    user = User(email="test@example.com", ...)
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
```

**Issues:**
- ✅ Docstring uses "Test #1" (with # symbol)
- ✅ Has `@pytest.mark.critical` marker
- ✅ Has section comments with separators
- ✅ Uses `db_session` fixture
- ❌ Marker is `@pytest.mark.foundation` (module-specific)

### Module 2: Auth Tests (85 tests)
**Location:** `tests/unit/auth/`

**Current Pattern:**
```python
"""
Module 2: Auth - User Controller Tests (Tests 274-298)

Tests user controller CRUD operations, OTP generation, and status transitions.
These tests verify the controller layer, NOT just the models.
"""
import pytest
from datetime import datetime

from controller.user import create_user
from tests.helpers.bug_reporter import report_production_bug

# ==============================================
# USER CREATION TESTS (Tests 274-280)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_create_user_with_email_only(db_session):
    """
    Test #274: Create user with email + minimal fields
    """
    user_data = UserCreate(display_name="Email User", ...)
    user = create_user(db_session, user_data)

    assert user.id is not None
```

**Issues:**
- ✅ Docstring uses "Test #274" (with # symbol)
- ✅ Has `@pytest.mark.critical` marker
- ✅ Has section comments with separators
- ✅ Uses `db_session` fixture
- ❌ Marker is `@pytest.mark.auth` (module-specific)

---

## STANDARD TEMPLATE

### File Header
```python
"""
Module X: [Module Name] - [Subsection] (Tests XXX-YYY)

[Brief description of what these tests validate]

Test Categories:
- Category 1: Description
- Category 2: Description
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Import models, controllers, schemas
from app.models.user import User, UserStatus
from app.controllers.user import create_user
from app.schemas.user import UserCreate
from tests.helpers.bug_reporter import report_production_bug
```

### Section Header
```python
# ==============================================================================
# SECTION NAME (Tests XXX-YYY)
# ==============================================================================
```

### Individual Test
```python
@pytest.mark.unit
@pytest.mark.moduleX  # Module-specific marker (orm, foundation, auth, etc.)
@pytest.mark.critical  # Optional: for critical/high-priority tests
def test_descriptive_name_of_what_is_tested(db_session):  # or other fixtures
    """
    Test #XXX: Clear one-line description of what is tested

    Optional additional context:
    - What scenario is being tested
    - What edge case is being validated
    - What bug this test would catch
    """
    # Arrange: Set up test data
    user = User(
        email="test@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Act: Perform the action being tested
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Assert: Verify expected outcomes
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.status == UserStatus.unknown
```

### Bug Reporting (when bug found)
```python
@pytest.mark.unit
@pytest.mark.moduleX
@pytest.mark.critical
def test_email_case_sensitivity(db_session):
    """
    Test #XXX: Email uniqueness should be case-insensitive

    This test checks if duplicate emails with different cases are prevented.
    Emails should follow RFC 5321 (case-insensitive).
    """
    # Arrange
    user1 = User(email="test@example.com", ...)
    db_session.add(user1)
    db_session.commit()

    user2 = User(email="Test@example.com", ...)  # Different case
    db_session.add(user2)

    # Act & Assert
    try:
        db_session.commit()
        # If we get here, bug found!
        report_production_bug(
            bug_number=1,
            title="Email Case Sensitivity",
            issue="Database allows duplicate emails with different cases",
            impact="Users can create multiple accounts bypassing uniqueness",
            fix="Use CITEXT column OR normalize emails to lowercase",
            location="models/user.py - email column definition"
        )
        # Cleanup
        db_session.delete(user2)
        db_session.delete(user1)
        db_session.commit()
        assert True  # Pass to continue finding bugs
    except IntegrityError:
        # Good! Database enforces uniqueness
        db_session.rollback()
        assert True
```

---

## STANDARDIZATION RULES

### 1. File Structure
```
"""Module header with description"""
import statements (grouped by: stdlib, third-party, app, test helpers)

# Section 1 Header
@pytest decorators
def test_function():
    """docstring"""
    # test code

# Section 2 Header
@pytest decorators
def test_function():
    ...
```

### 2. Naming Conventions
- **Test functions:** `test_<what>_<scenario>` (snake_case)
- **Fixtures:** snake_case (db_session, test_user, etc.)
- **Test numbers:** Sequential within module (Test #1, Test #2, ...)

### 3. Docstring Format
```python
"""
Test #XXX: One-line description starting with verb

Optional multi-line explanation:
- Additional context
- Edge cases covered
- Expected bugs this catches
"""
```

### 4. Markers (ALWAYS in this order)
```python
@pytest.mark.unit              # Always first (test level)
@pytest.mark.<module>          # Module marker (orm/foundation/auth/etc.)
@pytest.mark.critical          # Optional: critical priority tests
```

### 5. Test Structure (Arrange-Act-Assert)
```python
def test_something(db_session):
    """Test #X: Description"""

    # Arrange: Setup
    data = prepare_test_data()

    # Act: Execute
    result = function_under_test(data)

    # Assert: Verify
    assert result.expected_field == expected_value
```

### 6. Section Comments
```python
# ==============================================================================
# SECTION NAME (Tests XXX-YYY)
# ==============================================================================
```
- Use 78 characters width (=============)
- Include test range in parentheses
- One blank line before, none after

### 7. Import Organization
```python
# Standard library
import pytest
from datetime import datetime
from typing import Optional

# Third-party
from sqlalchemy.exc import IntegrityError

# Application imports
from app.models.user import User, UserStatus
from app.controllers.user import create_user
from app.schemas.user import UserCreate
from app.core.security import hash_password

# Test helpers (always last)
from tests.helpers.bug_reporter import report_production_bug
```

---

## CHECKLIST FOR STANDARDIZATION

For each test file, verify:

- [ ] File docstring matches template (Module X: Name - Subsection (Tests X-Y))
- [ ] Imports organized in 4 groups (stdlib, third-party, app, test helpers)
- [ ] Section comments use "==============" (78 chars) with test ranges
- [ ] All tests have 3 markers: @pytest.mark.unit, @pytest.mark.<module>, [@pytest.mark.critical]
- [ ] All docstrings use "Test #XXX:" format (with # symbol)
- [ ] All tests use Arrange-Act-Assert structure with comments
- [ ] All bug reports use `report_production_bug()` helper
- [ ] All assertions have meaningful failure messages
- [ ] All tests are independent (no shared state)
- [ ] All tests clean up after themselves

---

## MIGRATION PLAN

### Phase 1: Module 0 (ORM Tests)
- Add `@pytest.mark.critical` to all tests
- Change docstrings from "Test 1:" to "Test #1:"
- Add section comments with separators
- Add Arrange-Act-Assert comments

### Phase 2: Module 1 (Foundation Tests)
- Already mostly standardized
- Just need to verify consistency

### Phase 3: Module 2 (Auth Tests)
- Already mostly standardized
- Just need to verify consistency

### Phase 4: Future Modules
- Use standard template from the start
- Copy template as starting point

---

## EXAMPLE: Before & After

### BEFORE (Module 0 - Inconsistent)
```python
"""
ORM Tests for User Model
"""
import pytest
from sqlalchemy import inspect
from app.models.user import User

@pytest.mark.unit
@pytest.mark.orm
def test_user_model_table_name():
    """Test 1: Verify User model table name"""
    assert User.__tablename__ == "users"
```

### AFTER (Module 0 - Standardized)
```python
"""
Module 0: ORM Models - User Model (Tests 1-15)

Validates SQLAlchemy model schema, relationships, and constraints.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 1-8)
- Relationships (Tests 9-12)
- Constraints (Tests 13-15)
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime

from app.models.user import User, UserProfile, UserStatus


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 1-8)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_user_model_table_name():
    """
    Test #1: Verify User model table name is 'users'

    Validates that SQLAlchemy maps the User class to the correct table.
    Mismatch would cause all user queries to fail.
    """
    # Act & Assert
    assert User.__tablename__ == "users"
```

---

## NOTES

1. **Why standardize?**
   - Easier to read and maintain
   - Consistent patterns reduce cognitive load
   - Automated tools can parse consistently
   - New tests follow clear template

2. **What NOT to change:**
   - Test logic/assertions (only formatting)
   - Test numbers (keep sequential)
   - Fixture names (established conventions)

3. **Priority:**
   - High: Docstring format, markers, section comments
   - Medium: Import organization, AAA structure
   - Low: Comment style, whitespace
