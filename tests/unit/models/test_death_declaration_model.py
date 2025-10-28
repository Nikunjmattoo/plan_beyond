"""
ORM Tests for DeathDeclaration Model
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.death import (
    DeathDeclaration, DeathType, DeclarationState, LLMSafetyCheck,
    DeathReview, LegendLifecycle, Contest, Broadcast
)


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_table_name():
    """Test 67: Verify DeathDeclaration model table name is 'death_declarations'"""
    assert DeathDeclaration.__tablename__ == "death_declarations"


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_all_columns_exist():
    """Test 68: Verify all required columns exist in DeathDeclaration model"""
    mapper = inspect(DeathDeclaration)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'root_user_id', 'type', 'declared_by_contact_id',
        'message', 'media_ids', 'evidence_file_id', 'note',
        'llm_safety_check', 'state', 'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in DeathDeclaration model"


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_root_user_id_foreign_key():
    """Test 69: Verify root_user_id is a foreign key to users (root_user)"""
    mapper = inspect(DeathDeclaration)
    root_user_id_col = mapper.columns['root_user_id']

    # Check if it has foreign keys
    assert len(root_user_id_col.foreign_keys) > 0

    # Check that it references users.id
    fk = list(root_user_id_col.foreign_keys)[0]
    assert 'users.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_declarer_contact_id_foreign_key():
    """Test 70: Verify declared_by_contact_id is a foreign key to contacts (nullable)"""
    mapper = inspect(DeathDeclaration)
    declarer_col = mapper.columns['declared_by_contact_id']

    # Should be nullable
    assert declarer_col.nullable is True

    # Should have foreign key
    assert len(declarer_col.foreign_keys) > 0

    # Check that it references contacts.id
    fk = list(declarer_col.foreign_keys)[0]
    assert 'contacts.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_type_enum():
    """Test 71: Verify type column is Enum (soft/hard)"""
    mapper = inspect(DeathDeclaration)
    type_col = mapper.columns['type']

    # Check if it's an Enum type
    assert 'Enum' in str(type(type_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_state_enum():
    """Test 72: Verify state column is Enum"""
    mapper = inspect(DeathDeclaration)
    state_col = mapper.columns['state']

    # Check if it's an Enum type
    assert 'Enum' in str(type(state_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_message_nullable():
    """Test 73: Verify message column is nullable"""
    mapper = inspect(DeathDeclaration)
    message_col = mapper.columns['message']

    # message should be nullable
    assert message_col.nullable is True


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_evidence_file_nullable():
    """Test 74: Verify evidence_file_id is nullable"""
    mapper = inspect(DeathDeclaration)
    evidence_col = mapper.columns['evidence_file_id']

    # evidence should be nullable (not all declarations have evidence)
    assert evidence_col.nullable is True or evidence_col.nullable is None


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_root_user_relationship():
    """Test 75: Verify death.root_user relationship exists (implicit via FK)"""
    # This test verifies the foreign key exists which implies relationship capability
    mapper = inspect(DeathDeclaration)
    root_user_id_col = mapper.columns['root_user_id']
    assert len(root_user_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_declarer_relationship():
    """Test 76: Verify death.declarer relationship exists (implicit via FK)"""
    # This test verifies the foreign key exists which implies relationship capability
    mapper = inspect(DeathDeclaration)
    declarer_col = mapper.columns['declared_by_contact_id']
    assert len(declarer_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_death_type_enum_values():
    """Test 77: Verify DeathType enum has correct values"""
    assert hasattr(DeathType, 'soft')
    assert hasattr(DeathType, 'hard')

    assert DeathType.soft.value == 'soft'
    assert DeathType.hard.value == 'hard'


@pytest.mark.unit
@pytest.mark.orm
def test_declaration_state_enum_values():
    """Test 78: Verify DeclarationState enum has correct values"""
    assert hasattr(DeclarationState, 'pending_review')
    assert hasattr(DeclarationState, 'accepted')
    assert hasattr(DeclarationState, 'rejected')
    assert hasattr(DeclarationState, 'retracted')


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_timestamps():
    """Test 79: Verify created_at and updated_at columns exist"""
    mapper = inspect(DeathDeclaration)
    column_names = [col.key for col in mapper.columns]

    assert 'created_at' in column_names
    assert 'updated_at' in column_names


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_repr_method():
    """Test 80: Verify DeathDeclaration __repr__() method works"""
    death = DeathDeclaration(
        root_user_id=1,
        type=DeathType.soft
    )

    # Should not raise an error
    repr_str = repr(death)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_death_declaration_cascade_delete():
    """Test 81: Verify CASCADE delete on root_user_id"""
    mapper = inspect(DeathDeclaration)
    root_user_id_col = mapper.columns['root_user_id']

    # Get foreign key
    fk = list(root_user_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
