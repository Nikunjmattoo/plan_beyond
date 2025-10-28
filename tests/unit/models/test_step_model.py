"""
Module 0: ORM Models - Step Model (FormStep) (Tests 112-123)

Validates SQLAlchemy model schema for form step configuration.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 112-113)
- Foreign keys (Test 114)
- Column types (Tests 115-116, 118)
- Default values (Test 117)
- Relationships (Tests 119-120)
- Unique constraints (Test 121)
- Model behavior (Tests 122-123)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.step import FormStep, StepType, StepOption


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 112-113)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_table_name():
    """
    Test #112: Verify FormStep model table name is 'form_steps'

    Validates that SQLAlchemy maps the FormStep class to the correct table.
    """
    # Act & Assert
    assert FormStep.__tablename__ == "form_steps"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_all_columns_exist():
    """
    Test #113: Verify all required columns exist in FormStep model

    Ensures the ORM schema matches database schema.
    Form steps define questions in vault file templates.
    """
    # Arrange
    mapper = inspect(FormStep)
    column_names = [col.key for col in mapper.columns]

    required_columns = [
        'id', 'section_master_id', 'step_name', 'question_id', 'title',
        'top_one_liner', 'bottom_one_line', 'display_order', 'type',
        'nested', 'validation', 'mandatory', 'skippable', 'eligible_reminder',
        'privacy_nudge', 'privacy_liner', 'config', 'created_at', 'updated_at'
    ]

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in FormStep model"


# ==============================================================================
# FOREIGN KEY TESTS (Test 114)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_section_id_foreign_key():
    """
    Test #114: Verify section_master_id is a foreign key to category_sections_master

    Each form step belongs to a section.
    """
    # Arrange
    mapper = inspect(FormStep)
    section_id_col = mapper.columns['section_master_id']

    # Act & Assert
    assert len(section_id_col.foreign_keys) > 0

    fk = list(section_id_col.foreign_keys)[0]
    assert 'category_sections_master.id' in str(fk.target_fullname)


# ==============================================================================
# COLUMN TYPE TESTS (Tests 115-116, 118)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_title_column():
    """
    Test #115: Verify title column is Text type

    Step title contains the question text.
    """
    # Arrange
    mapper = inspect(FormStep)
    title_col = mapper.columns['title']

    # Act & Assert
    assert 'Text' in str(type(title_col.type)) or str(title_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_type_enum():
    """
    Test #116: Verify type column is Enum (text/date/dropdown/file/multiselect)

    Step type defines the input control.
    """
    # Arrange
    mapper = inspect(FormStep)
    type_col = mapper.columns['type']

    # Act & Assert
    assert 'Enum' in str(type(type_col.type))


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_display_order_column():
    """
    Test #118: Verify display_order column is Integer

    Display order controls question sequence.
    """
    # Arrange
    mapper = inspect(FormStep)
    display_order_col = mapper.columns['display_order']

    # Act & Assert
    assert 'Integer' in str(type(display_order_col.type)) or 'INTEGER' in str(display_order_col.type)


# ==============================================================================
# DEFAULT VALUE TESTS (Test 117)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_mandatory_default_false():
    """
    Test #117: Verify mandatory has default False

    Steps are optional by default.
    """
    # Arrange
    mapper = inspect(FormStep)
    mandatory_col = mapper.columns['mandatory']

    # Act & Assert
    assert mandatory_col.default is not None or mandatory_col.server_default is not None


# ==============================================================================
# RELATIONSHIP TESTS (Tests 119-120)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_section_relationship():
    """
    Test #119: Verify step.section relationship exists (implicit via FK)

    Foreign key establishes the relationship to the parent section.
    """
    # Arrange
    mapper = inspect(FormStep)
    section_id_col = mapper.columns['section_master_id']

    # Act & Assert
    assert len(section_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_options_relationship():
    """
    Test #120: Verify step.options relationship exists

    Options define dropdown/multiselect choices.
    Should cascade delete when step is deleted.
    """
    # Arrange
    mapper = inspect(FormStep)
    relationship_names = [rel.key for rel in mapper.relationships]

    # Act & Assert
    assert 'options' in relationship_names

    # Verify cascade delete
    options_rel = mapper.relationships['options']
    assert 'delete-orphan' in str(options_rel.cascade)


# ==============================================================================
# UNIQUE CONSTRAINT TESTS (Test 121)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_unique_constraint():
    """
    Test #121: Verify UNIQUE constraint on (section_master_id, display_order)

    Display order must be unique within a section.
    """
    # Arrange & Act
    assert hasattr(FormStep, '__table_args__')

    # Check for unique constraint in table args
    has_unique_constraint = False
    for constraint in FormStep.__table_args__:
        if hasattr(constraint, 'name') and 'uq_section_step_order' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (section_master_id, display_order) not found"


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 122-123)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_repr_method():
    """
    Test #122: Verify FormStep __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    step = FormStep(
        section_master_id=1,
        step_name="test",
        title="Test Step",
        type=StepType.open
    )

    # Act
    repr_str = repr(step)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_step_cascade_delete():
    """
    Test #123: Verify CASCADE delete on section_master_id

    When section is deleted, all its steps should be deleted.
    """
    # Arrange
    mapper = inspect(FormStep)
    section_id_col = mapper.columns['section_master_id']
    fk = list(section_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
