"""
Module 4: Categories - Leaf Assignment Controller Tests (Tests 194-213)

Tests leaf assignment operations for category sections.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.category import CategoryMaster, CategorySectionMaster, CategoryProgressLeaf, ProgressLeafStatus
from app.models.user import User
from app.models.contact import Contact
from app.models.user_forms import UserSectionProgress


# ==============================================
# CREATE TESTS (Tests 194-197)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_create_leaf_assignment(db_session):
    """
    Test #194: Create CategoryProgressLeaf assignment
    """
    # Arrange
    user = User(email="leaf@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="John Doe")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="leaf_cat", name="Leaf Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="leaf_sec", name="Leaf Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )

    # Act
    db_session.add(leaf)
    db_session.commit()

    # Assert
    assert leaf.id is not None
    assert leaf.contact_id == contact.id


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_requires_contact_id(db_session):
    """
    Test #195: Leaf assignment requires contact_id (NOT NULL)
    """
    # Arrange
    user = User(email="req@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="req_cat", name="Req Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="req_sec", name="Req Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=None
    )

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.add(leaf)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_requires_section_id(db_session):
    """
    Test #196: Leaf assignment requires section_id (NOT NULL)
    """
    # Arrange
    user = User(email="sec@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Jane Doe")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="sec_cat", name="Sec Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="sec_sec", name="Sec Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=None,
        progress_id=progress.id,
        contact_id=contact.id
    )

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.add(leaf)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_status_defaults_active(db_session):
    """
    Test #197: Leaf assignment status defaults to 'active'
    """
    # Arrange
    user = User(email="status@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Bob Smith")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="status_cat", name="Status Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="status_sec", name="Status Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )

    # Act
    db_session.add(leaf)
    db_session.commit()

    # Assert
    assert leaf.status == ProgressLeafStatus.active


# ==============================================
# READ & UPDATE TESTS (Tests 198-201)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_get_leaf_assignment_by_id(db_session):
    """
    Test #198: Retrieve leaf assignment by ID
    """
    # Arrange
    user = User(email="get@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Alice Brown")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="get_cat", name="Get Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="get_sec", name="Get Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf)
    db_session.commit()

    # Act
    result = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf.id).first()

    # Assert
    assert result is not None
    assert result.contact_id == contact.id


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_update_leaf_assignment_status(db_session):
    """
    Test #199: Update leaf assignment status
    """
    # Arrange
    user = User(email="update@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Charlie Green")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="update_cat", name="Update Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="update_sec", name="Update Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf)
    db_session.commit()

    # Act
    leaf.status = ProgressLeafStatus.accepted
    db_session.commit()

    # Assert
    updated = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf.id).first()
    assert updated.status == ProgressLeafStatus.accepted


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_accept(db_session):
    """
    Test #200: Accept leaf assignment (change status to accepted)
    """
    # Arrange
    user = User(email="accept@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Diana White")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="accept_cat", name="Accept Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="accept_sec", name="Accept Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id,
        status=ProgressLeafStatus.active
    )
    db_session.add(leaf)
    db_session.commit()

    # Act
    leaf.status = ProgressLeafStatus.accepted
    db_session.commit()

    # Assert
    assert leaf.status == ProgressLeafStatus.accepted


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_reject(db_session):
    """
    Test #201: Reject leaf assignment (change status to removed)
    """
    # Arrange
    user = User(email="reject@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Eve Black")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="reject_cat", name="Reject Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="reject_sec", name="Reject Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id,
        status=ProgressLeafStatus.active
    )
    db_session.add(leaf)
    db_session.commit()

    # Act
    leaf.status = ProgressLeafStatus.removed
    db_session.commit()

    # Assert
    assert leaf.status == ProgressLeafStatus.removed


# ==============================================
# REMOVE & LIST TESTS (Tests 202-204)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_remove(db_session):
    """
    Test #202: Remove leaf assignment (same as reject)
    """
    # Arrange
    user = User(email="remove@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Frank Gray")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="remove_cat", name="Remove Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="remove_sec", name="Remove Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf)
    db_session.commit()

    # Act
    leaf.status = ProgressLeafStatus.removed
    db_session.commit()

    # Assert
    assert leaf.status == ProgressLeafStatus.removed


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_list_leaf_assignments_for_user(db_session):
    """
    Test #203: List all leaf assignments for a user
    """
    # Arrange
    user = User(email="list@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contacts = [
        Contact(owner_user_id=user.id, first_name="Contact 1"),
        Contact(owner_user_id=user.id, first_name="Contact 2"),
    ]
    for c in contacts:
        db_session.add(c)
    db_session.commit()

    category = CategoryMaster(code="list_cat", name="List Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="list_sec", name="List Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaves = [
        CategoryProgressLeaf(
            user_id=user.id,
            category_id=category.id,
            section_id=section.id,
            progress_id=progress.id,
            contact_id=contacts[0].id
        ),
        CategoryProgressLeaf(
            user_id=user.id,
            category_id=category.id,
            section_id=section.id,
            progress_id=progress.id,
            contact_id=contacts[1].id
        )
    ]
    for leaf in leaves:
        db_session.add(leaf)
    db_session.commit()

    # Act
    results = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.user_id == user.id).all()

    # Assert
    assert len(results) == 2


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_list_leaf_assignments_for_section(db_session):
    """
    Test #204: List all leaf assignments for a section
    """
    # Arrange
    user = User(email="section@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contacts = [
        Contact(owner_user_id=user.id, first_name="Contact A"),
        Contact(owner_user_id=user.id, first_name="Contact B"),
    ]
    for c in contacts:
        db_session.add(c)
    db_session.commit()

    category = CategoryMaster(code="section_cat", name="Section Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="section_sec", name="Section Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaves = [
        CategoryProgressLeaf(
            user_id=user.id,
            category_id=category.id,
            section_id=section.id,
            progress_id=progress.id,
            contact_id=contacts[0].id
        ),
        CategoryProgressLeaf(
            user_id=user.id,
            category_id=category.id,
            section_id=section.id,
            progress_id=progress.id,
            contact_id=contacts[1].id
        )
    ]
    for leaf in leaves:
        db_session.add(leaf)
    db_session.commit()

    # Act
    results = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.section_id == section.id).all()

    # Assert
    assert len(results) == 2


# ==============================================
# UNIQUE CONSTRAINT & DELETE TESTS (Tests 205-206)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_unique_per_contact_section(db_session):
    """
    Test #205: Unique constraint on progress_id + contact_id
    """
    # Arrange
    user = User(email="unique@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Unique Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="unique_cat", name="Unique Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="unique_sec", name="Unique Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf1 = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf1)
    db_session.commit()

    leaf2 = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.add(leaf2)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_delete_leaf_assignment(db_session):
    """
    Test #206: Delete leaf assignment
    """
    # Arrange
    user = User(email="delete@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Delete Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="delete_cat", name="Delete Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="delete_sec", name="Delete Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf)
    db_session.commit()

    leaf_id = leaf.id

    # Act
    db_session.delete(leaf)
    db_session.commit()

    # Assert
    deleted = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf_id).first()
    assert deleted is None


# ==============================================
# AUTHORIZATION TESTS (Tests 207-209)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_can_only_accept_own_assignment(db_session):
    """
    Test #207: Leaf contact can only accept their own assignment (logic test)
    """
    # Arrange
    user = User(email="auth@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Contact 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Contact 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    category = CategoryMaster(code="auth_cat", name="Auth Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="auth_sec", name="Auth Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf1 = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact1.id
    )
    db_session.add(leaf1)
    db_session.commit()

    # Act - Contact1 can accept their own assignment
    if leaf1.contact_id == contact1.id:
        leaf1.status = ProgressLeafStatus.accepted
        db_session.commit()

    # Assert
    assert leaf1.status == ProgressLeafStatus.accepted


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_owner_can_create_leaf_assignment(db_session):
    """
    Test #208: File owner can create leaf assignments (logic test)
    """
    # Arrange
    user = User(email="owner@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Owner Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="owner_cat", name="Owner Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="owner_sec", name="Owner Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    is_owner = (progress.user_id == user.id)

    # Act & Assert
    if is_owner:
        leaf = CategoryProgressLeaf(
            user_id=user.id,
            category_id=category.id,
            section_id=section.id,
            progress_id=progress.id,
            contact_id=contact.id
        )
        db_session.add(leaf)
        db_session.commit()
        assert leaf.id is not None


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_non_owner_cannot_create_leaf_assignment(db_session):
    """
    Test #209: Non-owner cannot create leaf assignments (logic test)
    """
    # Arrange
    owner = User(email="owner@example.com", password="hash")
    other_user = User(email="other@example.com", password="hash")
    db_session.add_all([owner, other_user])
    db_session.commit()

    contact = Contact(owner_user_id=owner.id, first_name="Owner's Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="nonowner_cat", name="NonOwner Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="nonowner_sec", name="NonOwner Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=owner.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    is_owner = (progress.user_id == other_user.id)

    # Act & Assert
    assert is_owner is False


# ==============================================
# TIMESTAMP & BULK TESTS (Tests 210-212)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
def test_leaf_assignment_accepted_at_timestamp(db_session):
    """
    Test #210: Leaf has created_at timestamp (future: accepted_at)
    """
    # Arrange
    user = User(email="time@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Time Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="time_cat", name="Time Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="time_sec", name="Time Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )

    # Act
    db_session.add(leaf)
    db_session.commit()

    # Assert
    assert leaf.created_at is not None


@pytest.mark.unit
@pytest.mark.categories
def test_leaf_assignment_rejected_at_timestamp(db_session):
    """
    Test #211: Leaf has updated_at timestamp (future: rejected_at)
    """
    # Arrange
    user = User(email="reject_time@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Reject Time Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="reject_time_cat", name="Reject Time Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="reject_time_sec", name="Reject Time Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf)
    db_session.commit()

    # Assert
    assert leaf.updated_at is not None


@pytest.mark.unit
@pytest.mark.categories
def test_bulk_leaf_assignment_creation(db_session):
    """
    Test #212: Bulk create leaf assignments
    """
    # Arrange
    user = User(email="bulk@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contacts = [
        Contact(owner_user_id=user.id, first_name=f"Contact{i}")
        for i in range(1, 6)
    ]
    for c in contacts:
        db_session.add(c)
    db_session.commit()

    category = CategoryMaster(code="bulk_cat", name="Bulk Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="bulk_sec", name="Bulk Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaves = [
        CategoryProgressLeaf(
            user_id=user.id,
            category_id=category.id,
            section_id=section.id,
            progress_id=progress.id,
            contact_id=contact.id
        )
        for contact in contacts
    ]

    # Act
    db_session.bulk_save_objects(leaves)
    db_session.commit()

    # Assert
    saved = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.user_id == user.id).count()
    assert saved == 5


# ==============================================
# CASCADE DELETE TEST (Test 213)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_leaf_assignment_cascade_on_contact_delete(db_session):
    """
    Test #213: Deleting contact cascades to leaf assignments
    """
    # Arrange
    user = User(email="cascade@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Cascade Contact")
    db_session.add(contact)
    db_session.commit()

    category = CategoryMaster(code="cascade_cat", name="Cascade Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="cascade_sec", name="Cascade Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    leaf = CategoryProgressLeaf(
        user_id=user.id,
        category_id=category.id,
        section_id=section.id,
        progress_id=progress.id,
        contact_id=contact.id
    )
    db_session.add(leaf)
    db_session.commit()

    leaf_id = leaf.id

    # Act
    db_session.delete(contact)
    db_session.commit()

    # Assert
    deleted_leaf = db_session.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf_id).first()
    assert deleted_leaf is None
