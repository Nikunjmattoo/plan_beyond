#!/usr/bin/env python3
"""
Standalone Database Test - NO pip install required!
Just runs with Python + PostgreSQL
"""

import sys
import os

# Check if packages are installed
try:
    import pytest
    import sqlalchemy
    import psycopg2
except ImportError as e:
    print(f"Missing package: {e}")
    print("\nInstall these 3 packages only:")
    print("  pip install pytest sqlalchemy psycopg2-binary")
    print("\nThese work with Python 3.13!")
    sys.exit(1)

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, TIMESTAMP, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

# Database setup
TEST_DB_URL = "postgresql://test:test@localhost:5432/test_plan_beyond"
engine = create_engine(TEST_DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Define minimal models for testing
class UserStatus(str, enum.Enum):
    unknown = "unknown"
    guest = "guest"
    verified = "verified"
    member = "member"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.unknown)
    display_name = Column(String(255), nullable=True)
    country_code = Column(String(10), nullable=True)
    otp = Column(String(10), nullable=True)
    otp_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

# Tests
def test_database_connection():
    """Test we can connect to PostgreSQL"""
    session = SessionLocal()
    result = session.execute(sqlalchemy.text("SELECT 1"))
    assert result.fetchone()[0] == 1
    session.close()
    print("✓ Database connection works!")

def test_create_user():
    """Test creating a user"""
    # Create tables
    Base.metadata.create_all(engine)

    session = SessionLocal()

    # Create user
    user = User(
        email="test@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"

    # Cleanup
    session.delete(user)
    session.commit()
    session.close()

    print("✓ User creation works!")

def test_email_uniqueness():
    """Test email unique constraint"""
    Base.metadata.create_all(engine)
    session = SessionLocal()

    # Create first user
    user1 = User(
        email="unique@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(user1)
    session.commit()

    # Try duplicate email
    user2 = User(
        email="unique@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(user2)

    try:
        session.commit()
        assert False, "Should have raised IntegrityError"
    except Exception as e:
        assert "unique" in str(e).lower() or "duplicate" in str(e).lower()
        session.rollback()

    # Cleanup
    session.delete(user1)
    session.commit()
    session.close()

    print("✓ Email uniqueness constraint works!")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing PostgreSQL Database")
    print("="*50 + "\n")

    try:
        test_database_connection()
        test_create_user()
        test_email_uniqueness()

        print("\n" + "="*50)
        print("✓ ALL TESTS PASSED!")
        print("="*50 + "\n")

        print("Your PostgreSQL test database is working!")
        print("You can now run the full test suite.")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
