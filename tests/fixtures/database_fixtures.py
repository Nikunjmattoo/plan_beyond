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
from sqlalchemy.pool import NullPool
from typing import Generator
import time

from app.database import Base
from app.config import settings


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
        # SQLite fallback (in-memory)
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=NullPool
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
        session.execute(table.delete())
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
