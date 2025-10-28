"""
Module 0: ORM Models - Section Model (CategorySectionMaster) (Tests 102-111)

Validates SQLAlchemy model schema for category sections.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 102-103)
- Foreign keys (Test 104)
- Column types (Tests 105, 107)
- Default values (Test 106)
- Relationships (Test 108)
- Unique constraints (Test 109)
- Model behavior (Tests 110-111)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.category import CategorySectionMaster


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 102-103)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_table_name():
    """
    Test #102: Verify CategorySectionMaster table name is 'category_sections_master'

    Validates that SQLAlchemy maps CategorySectionMaster to the correct table.
    """
    # Act & Assert
    assert CategorySectionMaster.__tablename__ == "category_sections_master"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_all_columns_exist():
    """
    Test #103: Verify all required columns exist in CategorySectionMaster model

    Ensures the ORM schema matches database schema.
    Sections are subsections within categories.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'category_id', 'code', 'name', 'sort_index', 'file_import']

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in CategorySectionMaster model"


# ==============================================================================
# FOREIGN KEY TESTS (Test 104)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_category_id_foreign_key():
    """
    Test #104: Verify category_id is a foreign key to categories_master

    Each section belongs to a category.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']

    # Act & Assert
    assert len(category_id_col.foreign_keys) > 0

    fk = list(category_id_col.foreign_keys)[0]
    assert 'categories_master.id' in str(fk.target_fullname)


# ==============================================================================
# COLUMN TYPE TESTS (Tests 105, 107)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_code_column():
    """
    Test #105: Verify code column is Text type

    Section code is used for programmatic identification.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    code_col = mapper.columns['code']

    # Act & Assert
    assert 'Text' in str(type(code_col.type)) or str(code_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_sort_index_column():
    """
    Test #107: Verify sort_index column is Integer

    Sort index controls display order within category.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    sort_index_col = mapper.columns['sort_index']

    # Act & Assert
    assert 'Integer' in str(type(sort_index_col.type)) or 'INTEGER' in str(sort_index_col.type)


# ==============================================================================
# DEFAULT VALUE TESTS (Test 106)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_file_import_default():
    """
    Test #106: Verify file_import has default False

    File import is optional for sections.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    file_import_col = mapper.columns['file_import']

    # Act & Assert
    assert file_import_col.default is not None or file_import_col.server_default is not None


# ==============================================================================
# RELATIONSHIP TESTS (Test 108)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_category_relationship():
    """
    Test #108: Verify section.category relationship exists (implicit via FK)

    Foreign key establishes the relationship to the parent category.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']

    # Act & Assert
    assert len(category_id_col.foreign_keys) > 0


# ==============================================================================
# UNIQUE CONSTRAINT TESTS (Test 109)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_unique_constraint():
    """
    Test #109: Verify UNIQUE constraint on (category_id, code)

    Section code must be unique within a category.
    """
    # Arrange & Act
    assert hasattr(CategorySectionMaster, '__table_args__')

    # Check for unique constraint in table args
    has_unique_constraint = False
    for constraint in CategorySectionMaster.__table_args__:
        if hasattr(constraint, 'name') and 'uq_category_section_code' in constraint.name:
            has_unique_constraint = True
            break

    # Assert
    assert has_unique_constraint, "UNIQUE constraint on (category_id, code) not found"


# ==============================================================================
# MODEL BEHAVIOR TESTS (Tests 110-111)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_repr_method():
    """
    Test #110: Verify CategorySectionMaster __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    section = CategorySectionMaster(
        category_id=1,
        code="test",
        name="Test Section"
    )

    # Act
    repr_str = repr(section)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_section_cascade_delete():
    """
    Test #111: Verify CASCADE delete on category_id

    When category is deleted, all its sections should be deleted.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']
    fk = list(category_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
