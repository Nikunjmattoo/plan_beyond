from sqlalchemy import create_engine, Text, String as StringType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, ARRAY, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import json
import uuid
from app.config import settings

# Custom type that works with both PostgreSQL and SQLite
class CompatibleArray(TypeDecorator):
    """
    Array type that works with both PostgreSQL (ARRAY) and SQLite (JSON Text).
    - PostgreSQL: Uses native ARRAY type
    - SQLite: Stores as JSON text, deserializes to list
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        else:
            # SQLite: serialize to JSON
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        else:
            # SQLite: deserialize from JSON
            return json.loads(value)


class CompatibleUUID(TypeDecorator):
    """
    UUID type that works with both PostgreSQL (UUID) and SQLite (String).
    - PostgreSQL: Uses native UUID type
    - SQLite: Stores as string, converts to UUID object
    """
    impl = StringType
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(StringType(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        else:
            # SQLite: convert UUID to string
            return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        else:
            # SQLite: convert string to UUID
            return uuid.UUID(value) if isinstance(value, str) else value

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()