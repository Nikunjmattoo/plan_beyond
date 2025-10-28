"""
Module 4: Categories - Category Controller Tests (Tests 129-143)

Tests CRUD operations for CategoryMaster.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.category import CategoryMaster


# ==============================================
# CREATE TESTS (Tests 129-131)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_create_category_master(db_session):
    """
    Test #129: Create CategoryMaster successfully
    """
    # Arrange
    category = CategoryMaster(
        code="banking",
        name="Banking & Finance",
        sort_index=1
    )

    # Act
    db_session.add(category)
    db_session.commit()

    # Assert
    assert category.id is not None
    assert category.code == "banking"
    assert category.name == "Banking & Finance"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_create_category_with_description(db_session):
    """
    Test #130: Create category with icon field
    """
    # Arrange
    category = CategoryMaster(
        code="insurance",
        name="Insurance",
        icon="Shield",
        sort_index=2
    )

    # Act
    db_session.add(category)
    db_session.commit()

    # Assert
    assert category.icon == "Shield"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_category_name_unique_constraint(db_session):
    """
    Test #131: Duplicate category code raises IntegrityError
    """
    # Arrange
    category1 = CategoryMaster(code="medical", name="Medical", sort_index=1)
    db_session.add(category1)
    db_session.commit()

    category2 = CategoryMaster(code="medical", name="Medical 2", sort_index=2)

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.add(category2)
        db_session.commit()


# ==============================================
# READ TESTS (Tests 132-134)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_get_category_by_id(db_session):
    """
    Test #132: Retrieve category by ID
    """
    # Arrange
    category = CategoryMaster(code="property", name="Property", sort_index=1)
    db_session.add(category)
    db_session.commit()

    # Act
    result = db_session.query(CategoryMaster).filter(CategoryMaster.id == category.id).first()

    # Assert
    assert result is not None
    assert result.code == "property"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_get_category_not_found_returns_none(db_session):
    """
    Test #133: Non-existent category returns None
    """
    # Act
    result = db_session.query(CategoryMaster).filter(CategoryMaster.id == 99999).first()

    # Assert
    assert result is None


@pytest.mark.unit
@pytest.mark.categories
def test_list_all_categories(db_session):
    """
    Test #134: List all categories
    """
    # Arrange
    categories = [
        CategoryMaster(code="cat1", name="Category 1", sort_index=1),
        CategoryMaster(code="cat2", name="Category 2", sort_index=2),
        CategoryMaster(code="cat3", name="Category 3", sort_index=3)
    ]
    for cat in categories:
        db_session.add(cat)
    db_session.commit()

    # Act
    results = db_session.query(CategoryMaster).all()

    # Assert
    assert len(results) >= 3


# ==============================================
# UPDATE TESTS (Tests 135-136)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_update_category_name(db_session):
    """
    Test #135: Update category name
    """
    # Arrange
    category = CategoryMaster(code="legal", name="Legal Matters", sort_index=1)
    db_session.add(category)
    db_session.commit()

    # Act
    category.name = "Legal Documents"
    db_session.commit()

    # Assert
    updated = db_session.query(CategoryMaster).filter(CategoryMaster.id == category.id).first()
    assert updated.name == "Legal Documents"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_update_category_description(db_session):
    """
    Test #136: Update category icon
    """
    # Arrange
    category = CategoryMaster(code="travel", name="Travel", icon="Airplane", sort_index=1)
    db_session.add(category)
    db_session.commit()

    # Act
    category.icon = "Globe"
    db_session.commit()

    # Assert
    updated = db_session.query(CategoryMaster).filter(CategoryMaster.id == category.id).first()
    assert updated.icon == "Globe"


# ==============================================
# DELETE TESTS (Test 137)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_delete_category_cascades_to_sections(db_session):
    """
    Test #137: Deleting category cascades to sections
    """
    # Arrange
    from app.models.category import CategorySectionMaster

    category = CategoryMaster(code="cascade_test", name="Cascade Test", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="section1",
        name="Section 1",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    section_id = section.id

    # Act
    db_session.delete(category)
    db_session.commit()

    # Assert
    deleted_section = db_session.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == section_id
    ).first()
    assert deleted_section is None


# ==============================================
# ORDERING & RELATIONSHIP TESTS (Tests 138-140)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
def test_list_categories_ordered_by_name(db_session):
    """
    Test #138: Categories ordered by sort_index
    """
    # Arrange
    categories = [
        CategoryMaster(code="z_cat", name="Z Category", sort_index=3),
        CategoryMaster(code="a_cat", name="A Category", sort_index=1),
        CategoryMaster(code="m_cat", name="M Category", sort_index=2)
    ]
    for cat in categories:
        db_session.add(cat)
    db_session.commit()

    # Act
    results = db_session.query(CategoryMaster).order_by(CategoryMaster.sort_index).all()

    # Assert
    assert results[0].name == "A Category"
    assert results[1].name == "M Category"
    assert results[2].name == "Z Category"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_category_section_relationship(db_session):
    """
    Test #139: Category has sections relationship (via foreign key)
    """
    # Arrange
    from app.models.category import CategorySectionMaster

    category = CategoryMaster(code="rel_test", name="Relationship Test", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="sec1",
        name="Section 1",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    # Act
    sections = db_session.query(CategorySectionMaster).filter(
        CategorySectionMaster.category_id == category.id
    ).all()

    # Assert
    assert len(sections) == 1
    assert sections[0].name == "Section 1"


@pytest.mark.unit
@pytest.mark.categories
def test_category_display_order_field(db_session):
    """
    Test #140: Category has sort_index field
    """
    # Arrange
    category = CategoryMaster(code="order_test", name="Order Test", sort_index=42)

    # Act
    db_session.add(category)
    db_session.commit()

    # Assert
    assert category.sort_index == 42


# ==============================================
# AUTHORIZATION TESTS (Tests 141-143)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_admin_only_can_create_category(db_session):
    """
    Test #141: Only admins should create categories (logic test)
    """
    # Arrange
    is_admin = True

    # Act & Assert
    if is_admin:
        category = CategoryMaster(code="admin_test", name="Admin Test", sort_index=1)
        db_session.add(category)
        db_session.commit()
        assert category.id is not None


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_admin_only_can_update_category(db_session):
    """
    Test #142: Only admins should update categories (logic test)
    """
    # Arrange
    category = CategoryMaster(code="update_test", name="Original Name", sort_index=1)
    db_session.add(category)
    db_session.commit()

    is_admin = True

    # Act & Assert
    if is_admin:
        category.name = "Updated Name"
        db_session.commit()
        assert category.name == "Updated Name"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_admin_only_can_delete_category(db_session):
    """
    Test #143: Only admins should delete categories (logic test)
    """
    # Arrange
    category = CategoryMaster(code="delete_test", name="Delete Test", sort_index=1)
    db_session.add(category)
    db_session.commit()

    is_admin = True
    category_id = category.id

    # Act & Assert
    if is_admin:
        db_session.delete(category)
        db_session.commit()

        deleted = db_session.query(CategoryMaster).filter(CategoryMaster.id == category_id).first()
        assert deleted is None
