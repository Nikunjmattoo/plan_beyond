"""
ORM Tests for Category Models
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.category import CategoryMaster, CategorySectionMaster


@pytest.mark.unit
@pytest.mark.orm
def test_category_table_name():
    """Test 92: Verify CategoryMaster model table name is 'categories_master'"""
    assert CategoryMaster.__tablename__ == "categories_master"


@pytest.mark.unit
@pytest.mark.orm
def test_category_all_columns_exist():
    """Test 93: Verify all required columns exist in CategoryMaster model"""
    mapper = inspect(CategoryMaster)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'code', 'name', 'sort_index', 'icon']

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in CategoryMaster model"


@pytest.mark.unit
@pytest.mark.orm
def test_category_code_column_unique():
    """Test 94: Verify code column has UNIQUE constraint"""
    mapper = inspect(CategoryMaster)
    code_col = mapper.columns['code']
    assert code_col.unique is True


@pytest.mark.unit
@pytest.mark.orm
def test_category_name_nullable():
    """Test 95: Verify name column is NOT NULL"""
    mapper = inspect(CategoryMaster)
    name_col = mapper.columns['name']
    assert name_col.nullable is False


@pytest.mark.unit
@pytest.mark.orm
def test_category_sort_index_column():
    """Test 96: Verify sort_index column is Integer"""
    mapper = inspect(CategoryMaster)
    sort_index_col = mapper.columns['sort_index']
    assert 'Integer' in str(type(sort_index_col.type)) or 'INTEGER' in str(sort_index_col.type)


@pytest.mark.unit
@pytest.mark.orm
def test_category_section_table_name():
    """Test 97: Verify CategorySectionMaster table name"""
    assert CategorySectionMaster.__tablename__ == "category_sections_master"


@pytest.mark.unit
@pytest.mark.orm
def test_category_section_category_id_foreign_key():
    """Test 98: Verify category_id is a foreign key to categories_master"""
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']

    # Check if it has foreign keys
    assert len(category_id_col.foreign_keys) > 0

    # Check that it references categories_master.id
    fk = list(category_id_col.foreign_keys)[0]
    assert 'categories_master.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_category_repr_method():
    """Test 99: Verify CategoryMaster __repr__() method works"""
    category = CategoryMaster(
        code="test",
        name="Test Category"
    )

    # Should not raise an error
    repr_str = repr(category)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_category_section_cascade_delete():
    """Test 100: Verify CASCADE delete on category_id in sections"""
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']

    # Get foreign key
    fk = list(category_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'


@pytest.mark.unit
@pytest.mark.orm
def test_category_code_not_nullable():
    """Test 101: Verify code is NOT NULL"""
    mapper = inspect(CategoryMaster)
    code_col = mapper.columns['code']
    assert code_col.nullable is False
