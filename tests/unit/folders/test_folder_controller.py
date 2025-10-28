"""
Module 5: Folders - Folder Controller Tests (Tests 500-519)

Tests CRUD operations for Folder model and default folder creation.

Test Categories:
- Create operations (Tests 500-504)
- Read operations (Tests 505-508)
- Update operations (Tests 509-511)
- Delete operations (Tests 512-514)
- Default folders (Tests 515-519)
"""
# Standard library
import pytest
from datetime import datetime

# Third-party
from sqlalchemy.exc import IntegrityError

# Application imports
from controller.folder import (
    create_folder,
    update_folder,
    delete_folder,
    get_user_folders,
    get_folder,
    create_default_folders_for_user,
    DEFAULT_FOLDER_NAMES
)
from app.models.user import User, UserStatus
from app.models.folder import Folder
from app.models.contact import Contact
from app.schemas.folder import FolderCreate, FolderUpdate


# ==============================================================================
# FOLDER CREATE TESTS (Tests 500-504)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_folder_basic(db_session):
    """
    Test #500: Create a folder with basic name

    Verifies folder creation with minimal required fields.
    """
    # Arrange
    user = User(email="folder@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder_data = FolderCreate(name="My Important Documents")

    # Act
    folder = create_folder(db_session, user.id, folder_data)

    # Assert
    assert folder.id is not None
    assert folder.user_id == user.id
    assert folder.name == "My Important Documents"
    assert folder.created_at is not None
    assert folder.updated_at is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_folder_with_special_characters(db_session):
    """
    Test #501: Create folder with special characters in name

    Validates that folder names can contain special characters.
    """
    # Arrange
    user = User(email="special@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder_data = FolderCreate(name="Tax Returns (2020-2024) & Receipts #1")

    # Act
    folder = create_folder(db_session, user.id, folder_data)

    # Assert
    assert folder.name == "Tax Returns (2020-2024) & Receipts #1"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_folder_multiple_for_same_user(db_session):
    """
    Test #502: User can create multiple folders

    Verifies no limit on folder count per user.
    """
    # Arrange
    user = User(email="multi@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    folder1 = create_folder(db_session, user.id, FolderCreate(name="Folder 1"))
    folder2 = create_folder(db_session, user.id, FolderCreate(name="Folder 2"))
    folder3 = create_folder(db_session, user.id, FolderCreate(name="Folder 3"))

    # Assert
    assert folder1.id != folder2.id != folder3.id
    assert all(f.user_id == user.id for f in [folder1, folder2, folder3])


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_folder_same_name_different_users(db_session):
    """
    Test #503: Different users can have folders with same name

    Folder names are scoped to users, not globally unique.
    """
    # Arrange
    user1 = User(email="user1@test.com", status=UserStatus.verified)
    user2 = User(email="user2@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    # Act
    folder1 = create_folder(db_session, user1.id, FolderCreate(name="Will"))
    folder2 = create_folder(db_session, user2.id, FolderCreate(name="Will"))

    # Assert
    assert folder1.name == folder2.name == "Will"
    assert folder1.user_id != folder2.user_id


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_folder_timestamps_set(db_session):
    """
    Test #504: created_at and updated_at timestamps are set automatically

    Validates automatic timestamp generation.
    """
    # Arrange
    user = User(email="timestamps@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    before_create = datetime.utcnow()
    folder = create_folder(db_session, user.id, FolderCreate(name="Test"))
    after_create = datetime.utcnow()

    # Assert
    assert folder.created_at is not None
    assert folder.updated_at is not None
    assert before_create <= folder.created_at <= after_create
    assert before_create <= folder.updated_at <= after_create


# ==============================================================================
# FOLDER READ TESTS (Tests 505-508)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_get_user_folders_returns_all_folders(db_session):
    """
    Test #505: get_user_folders returns all folders for a user

    Verifies folder listing functionality.
    """
    # Arrange
    user = User(email="list@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder1 = create_folder(db_session, user.id, FolderCreate(name="Folder 1"))
    folder2 = create_folder(db_session, user.id, FolderCreate(name="Folder 2"))

    # Act
    folders = get_user_folders(db_session, user.id)

    # Assert
    assert len(folders) == 2
    folder_names = {f["name"] for f in folders}
    assert "Folder 1" in folder_names
    assert "Folder 2" in folder_names


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_get_user_folders_empty_list(db_session):
    """
    Test #506: get_user_folders returns empty list for user with no folders

    Edge case: new user with no folders.
    """
    # Arrange
    user = User(email="empty@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    folders = get_user_folders(db_session, user.id)

    # Assert
    assert folders == []


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_get_folder_returns_correct_folder(db_session):
    """
    Test #507: get_folder returns specific folder by ID

    Verifies single folder retrieval.
    """
    # Arrange
    user = User(email="getone@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Target"))

    # Act
    result = get_folder(db_session, user.id, folder.id)

    # Assert
    assert result is not None
    assert result["id"] == folder.id
    assert result["name"] == "Target"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_get_folder_wrong_user_returns_none(db_session):
    """
    Test #508: get_folder returns None if folder doesn't belong to user

    CRITICAL: Authorization check - users cannot access other users' folders.
    """
    # Arrange
    user1 = User(email="owner@test.com", status=UserStatus.verified)
    user2 = User(email="intruder@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Private"))

    # Act
    result = get_folder(db_session, user2.id, folder.id)

    # Assert
    assert result is None  # user2 cannot access user1's folder


# ==============================================================================
# FOLDER UPDATE TESTS (Tests 509-511)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_folder_name(db_session):
    """
    Test #509: Update folder name

    Verifies folder renaming functionality.
    """
    # Arrange
    user = User(email="update@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Old Name"))

    # Act
    updated = update_folder(db_session, user.id, folder.id, FolderUpdate(name="New Name"))

    # Assert
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.id == folder.id


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_folder_wrong_user_returns_none(db_session):
    """
    Test #510: Cannot update folder belonging to another user

    CRITICAL: Authorization check for update operations.
    """
    # Arrange
    user1 = User(email="owner2@test.com", status=UserStatus.verified)
    user2 = User(email="hacker@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Protected"))

    # Act
    result = update_folder(db_session, user2.id, folder.id, FolderUpdate(name="Hacked"))

    # Assert
    assert result is None

    # Verify folder unchanged
    folder_check = get_folder(db_session, user1.id, folder.id)
    assert folder_check["name"] == "Protected"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_folder_nonexistent_returns_none(db_session):
    """
    Test #511: Updating non-existent folder returns None

    Edge case handling.
    """
    # Arrange
    user = User(email="ghost@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    result = update_folder(db_session, user.id, 99999, FolderUpdate(name="Ghost"))

    # Assert
    assert result is None


# ==============================================================================
# FOLDER DELETE TESTS (Tests 512-514)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_folder_removes_folder(db_session):
    """
    Test #512: Delete folder removes it from database

    Verifies folder deletion functionality.
    """
    # Arrange
    user = User(email="delete@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="To Delete"))
    folder_id = folder.id

    # Act
    deleted = delete_folder(db_session, user.id, folder_id)

    # Assert
    assert deleted is not None
    assert get_folder(db_session, user.id, folder_id) is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_folder_wrong_user_returns_none(db_session):
    """
    Test #513: Cannot delete folder belonging to another user

    CRITICAL: Authorization check for delete operations.
    """
    # Arrange
    user1 = User(email="keep@test.com", status=UserStatus.verified)
    user2 = User(email="deleter@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Safe"))

    # Act
    result = delete_folder(db_session, user2.id, folder.id)

    # Assert
    assert result is None

    # Verify folder still exists
    assert get_folder(db_session, user1.id, folder.id) is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_folder_cascades_to_branches_and_leaves(db_session):
    """
    Test #514: Deleting folder cascades to branches and leaves

    CRITICAL: Cascade delete must work to prevent orphaned records.
    """
    # Arrange
    from app.models.folder import FolderBranch, FolderLeaf

    user = User(email="cascade@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Test Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Cascade Test"))

    # Add branch and leaf
    branch = FolderBranch(folder_id=folder.id, contact_id=contact.id)
    leaf = FolderLeaf(folder_id=folder.id, contact_id=contact.id)
    db_session.add_all([branch, leaf])
    db_session.commit()

    branch_id = branch.id
    leaf_id = leaf.id

    # Act
    delete_folder(db_session, user.id, folder.id)

    # Assert - branches and leaves should be deleted
    assert db_session.query(FolderBranch).filter(FolderBranch.id == branch_id).first() is None
    assert db_session.query(FolderLeaf).filter(FolderLeaf.id == leaf_id).first() is None


# ==============================================================================
# DEFAULT FOLDERS TESTS (Tests 515-519)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_default_folders_for_new_user(db_session):
    """
    Test #515: Default folders created for new user

    Verifies all default folders are created during signup.
    """
    # Arrange
    user = User(email="newuser@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    created = create_default_folders_for_user(db_session, user.id)

    # Assert
    assert len(created) == len(DEFAULT_FOLDER_NAMES)
    created_names = {f.name for f in created}
    assert created_names == set(DEFAULT_FOLDER_NAMES)


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_default_folder_names_are_correct(db_session):
    """
    Test #516: Default folder names match specification

    Verifies expected default folders: Will, Life Insurance, Cards.
    """
    # Arrange
    user = User(email="defaults@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    create_default_folders_for_user(db_session, user.id)
    folders = get_user_folders(db_session, user.id)

    # Assert
    folder_names = {f["name"] for f in folders}
    assert "Will" in folder_names
    assert "Life Insurance" in folder_names
    assert "Cards" in folder_names


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_default_folders_idempotent(db_session):
    """
    Test #517: Calling create_default_folders twice doesn't duplicate

    CRITICAL: Idempotency check - prevents duplicate defaults.
    """
    # Arrange
    user = User(email="idempotent@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    first_call = create_default_folders_for_user(db_session, user.id)
    second_call = create_default_folders_for_user(db_session, user.id)

    # Assert
    assert len(first_call) == 3
    assert len(second_call) == 0  # Nothing created on second call

    # Verify only 3 folders exist
    folders = get_user_folders(db_session, user.id)
    assert len(folders) == 3


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_default_folders_partial_existing(db_session):
    """
    Test #518: Default folder creation skips existing folders

    If user manually created "Will", default creation should skip it.
    """
    # Arrange
    user = User(email="partial@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # User already has "Will" folder
    create_folder(db_session, user.id, FolderCreate(name="Will"))

    # Act
    created = create_default_folders_for_user(db_session, user.id)

    # Assert
    assert len(created) == 2  # Only "Life Insurance" and "Cards" created
    created_names = {f.name for f in created}
    assert "Will" not in created_names
    assert "Life Insurance" in created_names
    assert "Cards" in created_names


@pytest.mark.unit
@pytest.mark.folders
def test_default_folders_belong_to_correct_user(db_session):
    """
    Test #519: Default folders are created for correct user only

    Verifies user isolation - defaults don't leak across users.
    """
    # Arrange
    user1 = User(email="user1_defaults@test.com", status=UserStatus.verified)
    user2 = User(email="user2_defaults@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    # Act
    create_default_folders_for_user(db_session, user1.id)

    # Assert
    user1_folders = get_user_folders(db_session, user1.id)
    user2_folders = get_user_folders(db_session, user2.id)

    assert len(user1_folders) == 3
    assert len(user2_folders) == 0  # user2 has no folders
