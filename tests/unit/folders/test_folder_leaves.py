"""
Module 5: Folders - Leaf Controller Tests (Tests 540-559)

Tests CRUD operations for FolderLeaf assignments with roles.

Test Categories:
- Add leaf (Tests 540-544)
- Update leaf (Tests 545-547)
- List/Delete leaves (Tests 548-550)
- Leaf roles (Tests 551-554)
- Uniqueness constraints (Tests 555-559)
"""
# Standard library
import pytest
from datetime import datetime

# Application imports
from controller.folder import (
    create_folder,
    add_leaf,
    update_leaf,
    list_leaves,
    delete_leaf
)
from app.models.user import User, UserStatus
from app.models.contact import Contact
from app.models.folder import AssignmentStatus, LeafRole
from app.schemas.folder import FolderCreate, LeafCreate, LeafUpdate


# ==============================================================================
# ADD LEAF TESTS (Tests 540-544)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_leaf_to_folder(db_session):
    """
    Test #540: Add leaf to folder successfully

    Verifies leaf assignment to folder.
    """
    # Arrange
    user = User(email="leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Leaf Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Test"))

    # Act
    leaf = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))

    # Assert
    assert leaf is not None
    assert leaf.folder_id == folder.id
    assert leaf.contact_id == contact.id
    assert leaf.role == LeafRole.leaf  # Default role
    assert leaf.status == AssignmentStatus.pending  # Default status


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_fallback_leaf(db_session):
    """
    Test #541: Add fallback leaf with fallback_leaf role

    Fallback leaves are secondary recipients.
    """
    # Arrange
    user = User(email="fallback@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Fallback")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Fallback Test"))

    # Act
    leaf = add_leaf(
        db_session, user.id, folder.id,
        LeafCreate(contact_id=contact.id, role=LeafRole.fallback_leaf)
    )

    # Assert
    assert leaf.role == LeafRole.fallback_leaf


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_leaf_duplicate_contact_fails(db_session):
    """
    Test #542: Cannot add same contact as leaf twice

    Uniqueness constraint on (folder_id, contact_id, role).
    """
    # Arrange
    user = User(email="dup_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Duplicate")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Dup"))

    # Act
    leaf1 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))
    leaf2 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))

    # Assert
    assert leaf1 is not None
    assert leaf2 is None  # Duplicate rejected


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_leaf_to_nonexistent_folder(db_session):
    """
    Test #543: Adding leaf to non-existent folder returns None

    Edge case handling.
    """
    # Arrange
    user = User(email="ghost_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Ghost")
    db_session.add(contact)
    db_session.commit()

    # Act
    leaf = add_leaf(db_session, user.id, 99999, LeafCreate(contact_id=contact.id))

    # Assert
    assert leaf is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_leaf_wrong_user_fails(db_session):
    """
    Test #544: Cannot add leaf to another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_leaf@test.com", status=UserStatus.verified)
    user2 = User(email="intruder_leaf@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    contact = Contact(owner_user_id=user2.id, first_name="Intruder")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Private"))

    # Act
    leaf = add_leaf(db_session, user2.id, folder.id, LeafCreate(contact_id=contact.id))

    # Assert
    assert leaf is None


# ==============================================================================
# UPDATE LEAF TESTS (Tests 545-547)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_leaf_status(db_session):
    """
    Test #545: Update leaf status from pending to active

    Verifies leaf status transitions.
    """
    # Arrange
    user = User(email="update_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Update")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Update"))
    leaf = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))

    # Act
    updated = update_leaf(
        db_session, user.id, folder.id, leaf.id,
        LeafUpdate(status=AssignmentStatus.active, accepted_at=datetime.utcnow())
    )

    # Assert
    assert updated is not None
    assert updated.status == AssignmentStatus.active
    assert updated.accepted_at is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_leaf_role(db_session):
    """
    Test #546: Update leaf role from leaf to fallback_leaf

    Allows changing leaf role after creation.
    """
    # Arrange
    user = User(email="role_change@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Role Change")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Role"))
    leaf = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, role=LeafRole.leaf))

    # Act
    updated = update_leaf(
        db_session, user.id, folder.id, leaf.id,
        LeafUpdate(role=LeafRole.fallback_leaf)
    )

    # Assert
    assert updated.role == LeafRole.fallback_leaf


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_leaf_wrong_user_fails(db_session):
    """
    Test #547: Cannot update leaf in another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_upd_leaf@test.com", status=UserStatus.verified)
    user2 = User(email="hacker_leaf@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    contact = Contact(owner_user_id=user1.id, first_name="Protected")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Protected"))
    leaf = add_leaf(db_session, user1.id, folder.id, LeafCreate(contact_id=contact.id))

    # Act
    result = update_leaf(
        db_session, user2.id, folder.id, leaf.id,
        LeafUpdate(status=AssignmentStatus.active)
    )

    # Assert
    assert result is None


# ==============================================================================
# LIST/DELETE LEAF TESTS (Tests 548-550)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_list_leaves_returns_all(db_session):
    """
    Test #548: list_leaves returns all leaves for a folder

    Verifies leaf listing.
    """
    # Arrange
    user = User(email="list_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Leaf 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Leaf 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="List"))
    add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact1.id))
    add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact2.id))

    # Act
    leaves = list_leaves(db_session, user.id, folder.id)

    # Assert
    assert leaves is not None
    assert len(leaves) == 2


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_leaf(db_session):
    """
    Test #549: Delete leaf from folder

    Verifies leaf deletion.
    """
    # Arrange
    user = User(email="del_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="To Delete")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Del"))
    leaf = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))

    # Act
    result = delete_leaf(db_session, user.id, folder.id, leaf.id)

    # Assert
    assert result is True
    leaves = list_leaves(db_session, user.id, folder.id)
    assert len(leaves) == 0


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_leaf_wrong_user_fails(db_session):
    """
    Test #550: Cannot delete leaf from another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_del_leaf@test.com", status=UserStatus.verified)
    user2 = User(email="deleter_leaf@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    contact = Contact(owner_user_id=user1.id, first_name="Safe")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Safe"))
    leaf = add_leaf(db_session, user1.id, folder.id, LeafCreate(contact_id=contact.id))

    # Act
    result = delete_leaf(db_session, user2.id, folder.id, leaf.id)

    # Assert
    assert result is False


# ==============================================================================
# LEAF ROLE TESTS (Tests 551-554)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_leaf_role_default_is_leaf(db_session):
    """
    Test #551: Default leaf role is 'leaf'

    Primary recipients are default.
    """
    # Arrange
    user = User(email="default_role@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Default")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Default"))

    # Act
    leaf = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))

    # Assert
    assert leaf.role == LeafRole.leaf


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_same_contact_both_roles_allowed(db_session):
    """
    Test #552: Same contact can have both leaf and fallback_leaf roles

    Uniqueness is on (folder, contact, role) triplet.
    """
    # Arrange
    user = User(email="both_roles@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Both")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Both"))

    # Act
    leaf1 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, role=LeafRole.leaf))
    leaf2 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, role=LeafRole.fallback_leaf))

    # Assert
    assert leaf1 is not None
    assert leaf2 is not None
    assert leaf1.role != leaf2.role


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_multiple_fallback_leaves_allowed(db_session):
    """
    Test #553: Folder can have multiple fallback leaves

    No limit on fallback leaf count.
    """
    # Arrange
    user = User(email="multi_fallback@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Fallback 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Fallback 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Multi"))

    # Act
    leaf1 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact1.id, role=LeafRole.fallback_leaf))
    leaf2 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact2.id, role=LeafRole.fallback_leaf))

    # Assert
    assert leaf1 is not None
    assert leaf2 is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_multiple_primary_leaves_allowed(db_session):
    """
    Test #554: Folder can have multiple primary leaves

    No limit on primary leaf count.
    """
    # Arrange
    user = User(email="multi_primary@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Primary 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Primary 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Primary"))

    # Act
    leaf1 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact1.id, role=LeafRole.leaf))
    leaf2 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact2.id, role=LeafRole.leaf))

    # Assert
    assert leaf1 is not None
    assert leaf2 is not None


# ==============================================================================
# UNIQUENESS CONSTRAINT TESTS (Tests 555-559)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_leaf_unique_per_folder_contact_role(db_session):
    """
    Test #555: Only one leaf per (folder, contact, role) triplet

    Database enforces uniqueness constraint.
    """
    # Arrange
    user = User(email="unique_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Unique")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Unique"))

    # Act
    leaf1 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, role=LeafRole.leaf))
    leaf2 = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, role=LeafRole.leaf))

    # Assert
    assert leaf1 is not None
    assert leaf2 is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_same_contact_different_folders_as_leaf(db_session):
    """
    Test #556: Same contact can be leaf in multiple folders

    Uniqueness is per folder.
    """
    # Arrange
    user = User(email="multi_folder_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Multi")
    db_session.add(contact)
    db_session.commit()

    folder1 = create_folder(db_session, user.id, FolderCreate(name="Folder 1"))
    folder2 = create_folder(db_session, user.id, FolderCreate(name="Folder 2"))

    # Act
    leaf1 = add_leaf(db_session, user.id, folder1.id, LeafCreate(contact_id=contact.id))
    leaf2 = add_leaf(db_session, user.id, folder2.id, LeafCreate(contact_id=contact.id))

    # Assert
    assert leaf1 is not None
    assert leaf2 is not None


@pytest.mark.unit
@pytest.mark.folders
def test_leaf_list_empty(db_session):
    """
    Test #557: list_leaves returns empty list for folder with no leaves

    Edge case.
    """
    # Arrange
    user = User(email="empty_leaves@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Empty"))

    # Act
    leaves = list_leaves(db_session, user.id, folder.id)

    # Assert
    assert leaves is not None
    assert len(leaves) == 0


@pytest.mark.unit
@pytest.mark.folders
def test_delete_nonexistent_leaf(db_session):
    """
    Test #558: Deleting non-existent leaf returns False

    Edge case handling.
    """
    # Arrange
    user = User(email="ghost_del_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Ghost"))

    # Act
    result = delete_leaf(db_session, user.id, folder.id, 99999)

    # Assert
    assert result is False


@pytest.mark.unit
@pytest.mark.folders
def test_leaf_accepted_at_timestamp(db_session):
    """
    Test #559: accepted_at timestamp set when leaf becomes active

    Tracks acceptance time.
    """
    # Arrange
    user = User(email="timestamp_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Timer")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Timer"))
    leaf = add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id))

    # Act
    before = datetime.utcnow()
    updated = update_leaf(
        db_session, user.id, folder.id, leaf.id,
        LeafUpdate(status=AssignmentStatus.active, accepted_at=datetime.utcnow())
    )
    after = datetime.utcnow()

    # Assert
    assert updated.accepted_at is not None
    assert before <= updated.accepted_at <= after
