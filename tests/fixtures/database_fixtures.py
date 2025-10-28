"""
Database fixtures for test isolation and cleanup.

Strategy:
1. Create a temporary test database (copy of original schema)
2. Run tests on the test database
3. Delete the test database after tests complete
"""
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, StaticPool
from typing import Generator
import time

from app.database import Base
from app.config import settings

# Import all model classes to register them with Base.metadata
from app.models.user import User, UserProfile  # noqa
from app.models.admin import Admin  # noqa
from app.models.contact import Contact  # noqa
from app.models.vault import VaultFile, VaultFileAccess  # noqa
from app.models.folder import Folder, FolderBranch, FolderLeaf, FolderTrigger  # noqa
from app.models.memory import MemoryCollection, MemoryFile, MemoryFileAssignment, MemoryCollectionAssignment  # noqa
from app.models.death import DeathAck, DeathDeclaration, DeathLock, LegendLifecycle, DeathReview, Contest, Broadcast, Config, AuditLog  # noqa
from app.models.trustee import Trustee  # noqa
from app.models.category import CategoryMaster, CategorySectionMaster, UserCategory, UserCategorySection, CategoryFile, CategoryLeafAssignment  # noqa
from app.models.reminder import Reminder  # noqa
from app.models.relationship import RelationshipRequest  # noqa
from app.models.card import SectionItemTemplate, UserSectionItem  # noqa
from app.models.death_approval import DeathApproval  # noqa
from app.models.release import Release, ReleaseRecipient  # noqa
from app.models.step import FormStep, StepOption  # noqa
from app.models.file import File  # noqa
from app.models.user_forms import UserSectionProgress, UserStepAnswer  # noqa
from app.models.verification import IdentityVerification, UserStatusHistory  # noqa
from app.models.reminder_preference import ReminderPreference  # noqa


def get_test_database_url() -> tuple[str, str]:
    """
    Generate a temporary test database URL.
    Returns: (test_db_url, test_db_name)
    """
    # Parse original DATABASE_URL
    original_url = settings.DATABASE_URL

    # For PostgreSQL: postgresql://user:pass@host:port/dbname
    # Extract base URL without database name
    if "postgresql" in original_url:
        parts = original_url.rsplit("/", 1)
        base_url = parts[0]
        original_db_name = parts[1] if len(parts) > 1 else "plan_beyond"

        # Create test database name with timestamp
        test_db_name = f"test_{original_db_name}_{int(time.time())}"
        test_db_url = f"{base_url}/{test_db_name}"

        return test_db_url, test_db_name

    # Fallback to SQLite for local testing
    else:
        return "sqlite:///:memory:", ":memory:"


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create a test database engine.
    This runs once per test session.

    Steps:
    1. Connect to default 'postgres' database
    2. Create temporary test database
    3. Apply schema from Base.metadata
    4. Yield engine for tests
    5. Drop test database after all tests
    """
    test_db_url, test_db_name = get_test_database_url()

    # Special handling for PostgreSQL
    if "postgresql" in settings.DATABASE_URL:
        # Connect to 'postgres' database to create test database
        base_url = settings.DATABASE_URL.rsplit("/", 1)[0]
        admin_url = f"{base_url}/postgres"

        admin_engine = create_engine(
            admin_url,
            isolation_level="AUTOCOMMIT",
            poolclass=NullPool
        )

        # Drop test database if it exists (cleanup from previous failed run)
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            print(f"\n[OK] Cleaned up any existing test database: {test_db_name}")

        # Create test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            print(f"[OK] Created test database: {test_db_name}")

        admin_engine.dispose()

        # Create engine for test database
        test_engine = create_engine(
            test_db_url,
            poolclass=NullPool,
            echo=False  # Set to True for SQL debugging
        )

        # Create all tables in test database
        Base.metadata.create_all(bind=test_engine)
        print(f"[OK] Created all tables in test database")

    else:
        # SQLite fallback (in-memory) - use StaticPool to keep single connection alive
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # Enable foreign key constraints for SQLite
        @event.listens_for(test_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Cleanup: Drop test database after all tests
    if "postgresql" in settings.DATABASE_URL:
        test_engine.dispose()

        # Reconnect to admin database to drop test database
        admin_engine = create_engine(
            admin_url,
            isolation_level="AUTOCOMMIT",
            poolclass=NullPool
        )

        with admin_engine.connect() as conn:
            # Terminate active connections to test database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                AND pid <> pg_backend_pid()
            """))

            # Drop test database
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            print(f"\n[OK] Dropped test database: {test_db_name}")

        admin_engine.dispose()
    else:
        test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a new database session for each test.
    Automatically rolls back after each test for isolation.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()

    yield session

    # Rollback any uncommitted changes
    session.rollback()

    # Clear all tables for next test (maintain isolation)
    for table in reversed(Base.metadata.sorted_tables):
        try:
            session.execute(table.delete())
        except Exception:
            # Skip tables that don't exist (e.g., in SQLite)
            pass
    session.commit()

    session.close()


@pytest.fixture
def clean_db(db_session):
    """
    Ensures database is clean before test runs.
    Automatically cleans up after test completes.
    """
    # Database is already clean from db_session fixture
    yield db_session


@pytest.fixture
def db_transaction(db_session):
    """
    Run test in a transaction that will be rolled back.
    Useful for tests that need to verify rollback behavior.
    """
    # Start a savepoint
    savepoint = db_session.begin_nested()

    yield db_session

    # Rollback to savepoint
    savepoint.rollback()


@pytest.fixture
def db_with_foreign_keys(test_db_engine):
    """
    Ensures foreign key constraints are enabled.
    (Mainly for SQLite, PostgreSQL has them enabled by default)
    """
    if "sqlite" in str(test_db_engine.url):
        @event.listens_for(test_db_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    yield test_db_engine


__all__ = [
    "test_db_engine",
    "db_session",
    "clean_db",
    "db_transaction",
    "db_with_foreign_keys",
]
