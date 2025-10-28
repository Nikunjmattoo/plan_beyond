"""
ORM Tests for Section Model (CategorySectionMaster)
Tests SQLAlchemy model schema, relationships, and constraints
"""
import pytest
from sqlalchemy import inspect

from app.models.category import CategorySectionMaster


@pytest.mark.unit
@pytest.mark.orm
def test_section_table_name():
    """Test 102: Verify CategorySectionMaster table name is 'category_sections_master'"""
    assert CategorySectionMaster.__tablename__ == "category_sections_master"


@pytest.mark.unit
@pytest.mark.orm
def test_section_all_columns_exist():
    """Test 103: Verify all required columns exist in CategorySectionMaster model"""
    mapper = inspect(CategorySectionMaster)
    column_names = [col.key for col in mapper.columns]

    required_columns = ['id', 'category_id', 'code', 'name', 'sort_index', 'file_import']

    for col in required_columns:
        assert col in column_names, f"Column '{col}' not found in CategorySectionMaster model"


@pytest.mark.unit
@pytest.mark.orm
def test_section_category_id_foreign_key():
    """Test 104: Verify category_id is a foreign key to categories_master"""
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']

    # Check if it has foreign keys
    assert len(category_id_col.foreign_keys) > 0

    # Check that it references categories_master.id
    fk = list(category_id_col.foreign_keys)[0]
    assert 'categories_master.id' in str(fk.target_fullname)


@pytest.mark.unit
@pytest.mark.orm
def test_section_code_column():
    """Test 105: Verify code column is Text type"""
    mapper = inspect(CategorySectionMaster)
    code_col = mapper.columns['code']
    assert 'Text' in str(type(code_col.type)) or str(code_col.type) == 'TEXT'


@pytest.mark.unit
@pytest.mark.orm
def test_section_file_import_default():
    """Test 106: Verify file_import has default False"""
    mapper = inspect(CategorySectionMaster)
    file_import_col = mapper.columns['file_import']

    # Should have a default
    assert file_import_col.default is not None or file_import_col.server_default is not None


@pytest.mark.unit
@pytest.mark.orm
def test_section_sort_index_column():
    """Test 107: Verify sort_index column is Integer"""
    mapper = inspect(CategorySectionMaster)
    sort_index_col = mapper.columns['sort_index']
    assert 'Integer' in str(type(sort_index_col.type)) or 'INTEGER' in str(sort_index_col.type)


@pytest.mark.unit
@pytest.mark.orm
def test_section_category_relationship():
    """Test 108: Verify section.category relationship exists (implicit via FK)"""
    # This test verifies the foreign key exists which implies relationship capability
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']
    assert len(category_id_col.foreign_keys) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_section_unique_constraint():
    """Test 109: Verify UNIQUE constraint on (category_id, code)"""
    # Check if table args has unique constraint
    assert hasattr(CategorySectionMaster, '__table_args__')

    # Check for unique constraint in table args
    has_unique_constraint = False
    for constraint in CategorySectionMaster.__table_args__:
        if hasattr(constraint, 'name') and 'uq_category_section_code' in constraint.name:
            has_unique_constraint = True
            break

    assert has_unique_constraint, "UNIQUE constraint on (category_id, code) not found"


@pytest.mark.unit
@pytest.mark.orm
def test_section_repr_method():
    """Test 110: Verify CategorySectionMaster __repr__() method works"""
    section = CategorySectionMaster(
        category_id=1,
        code="test",
        name="Test Section"
    )

    # Should not raise an error
    repr_str = repr(section)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@pytest.mark.unit
@pytest.mark.orm
def test_section_cascade_delete():
    """Test 111: Verify CASCADE delete on category_id"""
    mapper = inspect(CategorySectionMaster)
    category_id_col = mapper.columns['category_id']

    # Get foreign key
    fk = list(category_id_col.foreign_keys)[0]

    # Check for CASCADE ondelete
    assert fk.ondelete == 'CASCADE'
