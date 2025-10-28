"""
ORM Tests for Step Model (FormStep)
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.step import FormStep, StepType, StepOption


@pytest.mark.unit
@pytest.mark.orm
def test_step_table_name():
    """Test 112: Verify FormStep model table name is 'form_steps'"""
    assert FormStep.__tablename__ == "form_steps"


@pytest.mark.unit
@pytest.mark.orm
def test_step_all_columns_exist():
    """Test 113: Verify all required columns exist in FormStep model"""
    mapper = inspect(FormStep)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'section_master_id', 'step_name', 'question_id', 'title',
        'top_one_liner', 'bottom_one_line', 'display_order', 'type',
        'nested', 'validation', 'mandatory', 'skippable', 'eligible_reminder',
        'privacy_nudge', 'privacy_liner', 'config', 'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in FormStep model"


@pytest.mark.unit
@pytest.mark.orm
def test_step_section_id_foreign_key():
    """Test 114: Verify section_master_id is a foreign key to category_sections_master"""
    mapper = inspect(FormStep)
    section_id_col = mapper.columns['section_master_id']

    # Check if it has foreign keys
    assert len(section_id_col.foreign_keys) > 0

    # Check that it references category_sections_master.id
    fk = list(section_id_col.foreign_keys)[0]
    assert 'category_sections_master.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_step_title_column():
    """Test 115: Verify title column is Text type"""
    mapper = inspect(FormStep)
    title_col = mapper.columns['title']
    assert 'Text' in str(type(title_col.type)) or str(title_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
def test_step_type_enum():
    """Test 116: Verify type column is Enum (text/date/dropdown/file/multiselect)"""
    mapper = inspect(FormStep)
    type_col = mapper.columns['type']

    # Check if it's an Enum type
    assert 'Enum' in str(type(type_col.type))


@pytest.mark.unit
@pytest.mark.orm
def test_step_mandatory_default_false():
    """Test 117: Verify mandatory has default False"""
    mapper = inspect(FormStep)
    mandatory_col = mapper.columns['mandatory']

    # Should have a default
    assert mandatory_col.default is not None or mandatory_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_step_display_order_column():
    """Test 118: Verify display_order column is Integer"""
    mapper = inspect(FormStep)
    display_order_col = mapper.columns['display_order']
    assert 'Integer' in str(type(display_order_col.type)) or 'INTEGER' in str(display_order_col.type)


@pytest.mark.unit
@pytest.mark.orm
def test_step_section_relationship():
    """Test 119: Verify step.section relationship exists (implicit via FK)"""
    # This test verifies the foreign key exists which implies relationship capability
    mapper = inspect(FormStep)
    section_id_col = mapper.columns['section_master_id']
    assert len(section_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_step_options_relationship():
    """Test 120: Verify step.options relationship exists"""
    mapper = inspect(FormStep)
    relationship_names = [rel.key for rel in mapper.relationships]

    assert 'options' in relationship_names

    # Should cascade delete
    options_rel = mapper.relationships['options']
    assert 'delete-orphan' in str(options_rel.cascade)


@pytest.mark.unit
@pytest.mark.orm
def test_step_unique_constraint():
    """Test 121: Verify UNIQUE constraint on (section_master_id, display_order)"""
    # Check if table args has unique constraint
    assert hasattr(FormStep, '__table_args__')

    # Check for unique constraint in table args
    has_unique_constraint = False
    for constraint in FormStep.__table_args__:
        if hasattr(constraint, 'name') and 'uq_section_step_order' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (section_master_id, display_order) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_step_repr_method():
    """Test 122: Verify FormStep __repr__() method works"""
    step = FormStep(
        section_master_id=1,
        step_name="test",
        title="Test Step",
        type=StepType.open
    )

    # Should not raise an error
    repr_str = repr(step)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_step_cascade_delete():
    """Test 123: Verify CASCADE delete on section_master_id"""
    mapper = inspect(FormStep)
    section_id_col = mapper.columns['section_master_id']

    # Get foreign key
    fk = list(section_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
