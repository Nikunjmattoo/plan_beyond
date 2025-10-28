"""
Module 0: ORM Models - Category Models (Tests 92-101)

Validates SQLAlchemy model schema for category master data.
Does NOT create database records - only validates ORM definitions.

Test Categories:
- Schema validation (Tests 92-93, 97)
- Column constraints (Tests 94-96, 101)
- Foreign keys (Test 98)
- Model behavior (Tests 99-100)
"""
import pytest

# Third-party
from sqlalchemy import inspect

# Application imports
from app.models.category import CategoryMaster, CategorySectionMaster


# ==============================================================================
# SCHEMA VALIDATION TESTS (Tests 92-93, 97)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_table_name():
    """
    Test #92: Verify CategoryMaster model table name is 'categories_master'

    Validates that SQLAlchemy maps the CategoryMaster class to the correct table.
    """
    # Act & Assert
    assert CategoryMaster.__tablename__ == "categories_master"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_all_columns_exist():
    """
    Test #93: Verify all required columns exist in CategoryMaster model

    Ensures the ORM schema matches database schema.
    Categories organize vault file templates.
    """
    # Arrange
    mapper = inspect(CategoryMaster)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'code', 'name', 'sort_index', 'icon']

    # Act & Assert
    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in CategoryMaster model"


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_section_table_name():
    """
    Test #97: Verify CategorySectionMaster table name

    Validates that SQLAlchemy maps CategorySectionMaster to correct table.
    """
    # Act & Assert
    assert CategorySectionMaster.__tablename__ == "category_sections_master"


# ==============================================================================
# COLUMN CONSTRAINT TESTS (Tests 94-96, 101)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_code_column_unique():
    """
    Test #94: Verify code column has UNIQUE constraint

    Category codes must be unique system-wide.
    """
    # Arrange
    mapper = inspect(CategoryMaster)
    code_col = mapper.columns['code']

    # Act & Assert
    assert code_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_name_nullable():
    """
    Test #95: Verify name column is NOT NULL

    Category name is required.
    """
    # Arrange
    mapper = inspect(CategoryMaster)
    name_col = mapper.columns['name']

    # Act & Assert
    assert name_col.nullable is False


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_sort_index_column():
    """
    Test #96: Verify sort_index column is Integer

    Sort index controls display order.
    """
    # Arrange
    mapper = inspect(CategoryMaster)
    sort_index_col = mapper.columns['sort_index']

    # Act & Assert
    assert 'Integer' in str(type(sort_index_col.type)) or 'INTEGER' in str(sort_index_col.type)


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_code_not_nullable():
    """
    Test #101: Verify code is NOT NULL

    Category code is required.
    """
    # Arrange
    mapper = inspect(CategoryMaster)
    code_col = mapper.columns['code']

    # Act & Assert
    assert code_col.nullable is False


# ==============================================================================
# FOREIGN KEY TESTS (Test 98)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_section_category_id_foreign_key():
    """
    Test #98: Verify category_id is a foreign key to categories_master

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
# MODEL BEHAVIOR TESTS (Tests 99-100)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_repr_method():
    """
    Test #99: Verify CategoryMaster __repr__() method works

    Ensures model has readable string representation for debugging.
    """
    # Arrange
    category = CategoryMaster(
        code="test",
        name="Test Category"
    )

    # Act
    repr_str = repr(category)

    # Assert
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
@pytest.mark.critical
def test_category_section_cascade_delete():
    """
    Test #100: Verify CASCADE delete on category_id in sections

    When category is deleted, all its sections should be deleted.
    """
    # Arrange
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']
    fk = list(category_id_col.foreign_keys)[0]

    # Act & Assert
    assert fk.ondelete == 'CASCADE'
