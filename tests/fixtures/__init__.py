"""
Fixtures package for Plan Beyond test suite.

This package contains reusable test fixtures organized by domain:
- database_fixtures: Database session and cleanup
- user_fixtures: User, admin, contact, and profile fixtures
- auth_fixtures: Authentication tokens, OTP, and session fixtures
- vault_fixtures: Encrypted vault file fixtures
- mock_fixtures: Mocked external services (AWS, SMTP, Twilio, Google)
- factory_fixtures: Factory Boy factories for model generation
"""

# Import all fixtures to make them available when importing from fixtures
from .database_fixtures import *
from .user_fixtures import *
from .auth_fixtures import *
from .vault_fixtures import *
from .mock_fixtures import *
from .factory_fixtures import *
