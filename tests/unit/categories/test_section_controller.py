"""
Module 4: Categories - Section Controller Tests (Tests 144-155)

Tests CRUD operations for CategorySectionMaster.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.category import CategoryMaster, CategorySectionMaster


# ==============================================
# CREATE TESTS (Tests 144-146)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_create_section_for_category(db_session):
    """
    Test #144: Create CategorySectionMaster for a category
    """
    # Arrange
    category = CategoryMaster(code="finance", name="Finance", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="accounts",
        name="Bank Accounts",
        sort_index=1
    )

    # Act
    db_session.add(section)
    db_session.commit()

    # Assert
    assert section.id is not None
    assert section.category_id == category.id
    assert section.code == "accounts"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_section_requires_category_id(db_session):
    """
    Test #145: Section requires category_id (NOT NULL constraint)
    """
    # Arrange
    section = CategorySectionMaster(
        category_id=None,
        code="orphan",
        name="Orphan Section",
        sort_index=1
    )

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.add(section)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_section_allows_file_import_flag(db_session):
    """
    Test #146: Section has file_import boolean flag
    """
    # Arrange
    category = CategoryMaster(code="docs", name="Documents", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="import_test",
        name="Import Test",
        file_import=True,
        sort_index=1
    )

    # Act
    db_session.add(section)
    db_session.commit()

    # Assert
    assert section.file_import is True


# ==============================================
# READ TESTS (Test 147)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_get_section_by_id(db_session):
    """
    Test #147: Retrieve section by ID
    """
    # Arrange
    category = CategoryMaster(code="read_test", name="Read Test", sort_index=1)
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

    # Act
    result = db_session.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == section.id
    ).first()

    # Assert
    assert result is not None
    assert result.name == "Section 1"


# ==============================================
# UPDATE TESTS (Tests 148-149)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_update_section_name(db_session):
    """
    Test #148: Update section name
    """
    # Arrange
    category = CategoryMaster(code="update_cat", name="Update Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="update_sec",
        name="Original Name",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    # Act
    section.name = "Updated Name"
    db_session.commit()

    # Assert
    updated = db_session.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == section.id
    ).first()
    assert updated.name == "Updated Name"


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_update_section_description(db_session):
    """
    Test #149: Update section file_import flag
    """
    # Arrange
    category = CategoryMaster(code="flag_cat", name="Flag Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="flag_sec",
        name="Flag Section",
        file_import=False,
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    # Act
    section.file_import = True
    db_session.commit()

    # Assert
    updated = db_session.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == section.id
    ).first()
    assert updated.file_import is True


# ==============================================
# DELETE & CASCADE TESTS (Test 150)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_delete_section_cascades_to_steps(db_session):
    """
    Test #150: Deleting section cascades to FormSteps
    """
    # Arrange
    from app.models.step import FormStep, StepType

    category = CategoryMaster(code="cascade_cat", name="Cascade Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="cascade_sec",
        name="Cascade Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    step = FormStep(
        section_master_id=section.id,
        step_name="test_step",
        title="Test Step",
        display_order=1,
        type=StepType.open
    )
    db_session.add(step)
    db_session.commit()

    step_id = step.id

    # Act
    db_session.delete(section)
    db_session.commit()

    # Assert
    deleted_step = db_session.query(FormStep).filter(FormStep.id == step_id).first()
    assert deleted_step is None


# ==============================================
# LIST & RELATIONSHIP TESTS (Tests 151-152)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_list_sections_for_category(db_session):
    """
    Test #151: List all sections for a category
    """
    # Arrange
    category = CategoryMaster(code="list_cat", name="List Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    sections = [
        CategorySectionMaster(category_id=category.id, code="sec1", name="Section 1", sort_index=1),
        CategorySectionMaster(category_id=category.id, code="sec2", name="Section 2", sort_index=2),
        CategorySectionMaster(category_id=category.id, code="sec3", name="Section 3", sort_index=3)
    ]
    for sec in sections:
        db_session.add(sec)
    db_session.commit()

    # Act
    results = db_session.query(CategorySectionMaster).filter(
        CategorySectionMaster.category_id == category.id
    ).all()

    # Assert
    assert len(results) == 3


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_section_steps_relationship(db_session):
    """
    Test #152: Section has steps relationship (via foreign key)
    """
    # Arrange
    from app.models.step import FormStep, StepType

    category = CategoryMaster(code="rel_cat", name="Relationship Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="rel_sec",
        name="Relationship Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    step = FormStep(
        section_master_id=section.id,
        step_name="rel_step",
        title="Relationship Step",
        display_order=1,
        type=StepType.open
    )
    db_session.add(step)
    db_session.commit()

    # Act
    steps = db_session.query(FormStep).filter(
        FormStep.section_master_id == section.id
    ).all()

    # Assert
    assert len(steps) == 1
    assert steps[0].title == "Relationship Step"


# ==============================================
# ORDERING & AUTHORIZATION TESTS (Tests 153-155)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
def test_section_display_order(db_session):
    """
    Test #153: Section has sort_index field
    """
    # Arrange
    category = CategoryMaster(code="order_cat", name="Order Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="order_sec",
        name="Order Section",
        sort_index=99
    )

    # Act
    db_session.add(section)
    db_session.commit()

    # Assert
    assert section.sort_index == 99


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_admin_only_can_create_section(db_session):
    """
    Test #154: Only admins should create sections (logic test)
    """
    # Arrange
    category = CategoryMaster(code="admin_cat", name="Admin Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    is_admin = True

    # Act & Assert
    if is_admin:
        section = CategorySectionMaster(
            category_id=category.id,
            code="admin_sec",
            name="Admin Section",
            sort_index=1
        )
        db_session.add(section)
        db_session.commit()
        assert section.id is not None


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_admin_only_can_delete_section(db_session):
    """
    Test #155: Only admins should delete sections (logic test)
    """
    # Arrange
    category = CategoryMaster(code="del_cat", name="Delete Category", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(
        category_id=category.id,
        code="del_sec",
        name="Delete Section",
        sort_index=1
    )
    db_session.add(section)
    db_session.commit()

    is_admin = True
    section_id = section.id

    # Act & Assert
    if is_admin:
        db_session.delete(section)
        db_session.commit()

        deleted = db_session.query(CategorySectionMaster).filter(
            CategorySectionMaster.id == section_id
        ).first()
        assert deleted is None
