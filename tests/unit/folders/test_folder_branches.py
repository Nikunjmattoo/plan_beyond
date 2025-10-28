"""
Module 5: Folders - Branch Controller Tests (Tests 520-539)

Tests CRUD operations for FolderBranch assignments.

Test Categories:
- Add branch (Tests 520-524)
- Update branch (Tests 525-527)
- List branches (Tests 528-529)
- Delete branch (Tests 530-532)
- Branch status transitions (Tests 533-536)
- Uniqueness constraints (Tests 537-539)
"""
# Standard library
import pytest
from datetime import datetime

# Third-party
from sqlalchemy.exc import IntegrityError

# Application imports
from controller.folder import (
    create_folder,
    add_branch,
    update_branch,
    list_branches,
    delete_branch
)
from app.models.user import User, UserStatus
from app.models.contact import Contact
from app.models.folder import AssignmentStatus
from app.schemas.folder import FolderCreate, BranchCreate, BranchUpdate


# ==============================================================================
# ADD BRANCH TESTS (Tests 520-524)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_branch_to_folder(db_session):
    """
    Test #520: Add branch to folder successfully

    Verifies branch assignment to folder.
    """
    # Arrange
    user = User(email="branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Branch Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Test"))

    # Act
    branch, error = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Assert
    assert error is None
    assert branch is not None
    assert branch.folder_id == folder.id
    assert branch.contact_id == contact.id
    assert branch.status == AssignmentStatus.pending


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_branch_with_active_status(db_session):
    """
    Test #521: Add branch with active status immediately

    Verifies branches can be created as active (already accepted).
    """
    # Arrange
    user = User(email="active_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Active Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Active Test"))

    # Act
    branch, error = add_branch(
        db_session, user.id, folder.id,
        BranchCreate(contact_id=contact.id, status=AssignmentStatus.active, accepted_at=datetime.utcnow())
    )

    # Assert
    assert error is None
    assert branch.status == AssignmentStatus.active
    assert branch.accepted_at is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_branch_duplicate_contact_fails(db_session):
    """
    Test #522: Cannot add same contact as branch twice

    CRITICAL: Uniqueness constraint on (folder_id, contact_id).
    """
    # Arrange
    user = User(email="dup_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Duplicate")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Dup Test"))

    # Act
    branch1, error1 = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))
    branch2, error2 = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Assert
    assert branch1 is not None
    assert error1 is None
    assert branch2 is None
    assert error2 == "branch_exists"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_branch_to_nonexistent_folder(db_session):
    """
    Test #523: Adding branch to non-existent folder fails

    Edge case handling.
    """
    # Arrange
    user = User(email="ghost_folder@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Ghost Contact")
    db_session.add(contact)
    db_session.commit()

    # Act
    branch, error = add_branch(db_session, user.id, 99999, BranchCreate(contact_id=contact.id))

    # Assert
    assert branch is None
    assert error == "folder_not_found"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_add_branch_wrong_user_fails(db_session):
    """
    Test #524: Cannot add branch to another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_branch@test.com", status=UserStatus.verified)
    user2 = User(email="intruder_branch@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    contact = Contact(owner_user_id=user2.id, first_name="Intruder Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Private"))

    # Act
    branch, error = add_branch(db_session, user2.id, folder.id, BranchCreate(contact_id=contact.id))

    # Assert
    assert branch is None
    assert error == "folder_not_found"


# ==============================================================================
# UPDATE BRANCH TESTS (Tests 525-527)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_branch_status(db_session):
    """
    Test #525: Update branch status from pending to active

    Verifies branch status transitions.
    """
    # Arrange
    user = User(email="update_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Update Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Update Test"))
    branch, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    updated = update_branch(
        db_session, user.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.active, accepted_at=datetime.utcnow())
    )

    # Assert
    assert updated is not None
    assert updated.status == AssignmentStatus.active
    assert updated.accepted_at is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_branch_to_declined(db_session):
    """
    Test #526: Update branch status to declined

    Contact declined the branch assignment.
    """
    # Arrange
    user = User(email="declined_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Decliner")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Decline Test"))
    branch, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    updated = update_branch(
        db_session, user.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.declined)
    )

    # Assert
    assert updated.status == AssignmentStatus.declined


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_branch_wrong_user_fails(db_session):
    """
    Test #527: Cannot update branch in another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_upd@test.com", status=UserStatus.verified)
    user2 = User(email="hacker_upd@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    contact = Contact(owner_user_id=user1.id, first_name="Protected")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Protected"))
    branch, _ = add_branch(db_session, user1.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    result = update_branch(
        db_session, user2.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.active)
    )

    # Assert
    assert result is None


# ==============================================================================
# LIST BRANCHES TESTS (Tests 528-529)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_list_branches_returns_all(db_session):
    """
    Test #528: list_branches returns all branches for a folder

    Verifies branch listing.
    """
    # Arrange
    user = User(email="list_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Contact 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Contact 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="List Test"))
    add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact1.id))
    add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact2.id))

    # Act
    branches = list_branches(db_session, user.id, folder.id)

    # Assert
    assert branches is not None
    assert len(branches) == 2


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_list_branches_empty(db_session):
    """
    Test #529: list_branches returns empty list for folder with no branches

    Edge case: folder with no branches assigned.
    """
    # Arrange
    user = User(email="empty_branches@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Empty"))

    # Act
    branches = list_branches(db_session, user.id, folder.id)

    # Assert
    assert branches is not None
    assert len(branches) == 0


# ==============================================================================
# DELETE BRANCH TESTS (Tests 530-532)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_branch(db_session):
    """
    Test #530: Delete branch from folder

    Verifies branch deletion.
    """
    # Arrange
    user = User(email="del_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="To Delete")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Del Test"))
    branch, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    result = delete_branch(db_session, user.id, folder.id, branch.id)

    # Assert
    assert result is True
    branches = list_branches(db_session, user.id, folder.id)
    assert len(branches) == 0


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_branch_wrong_user_fails(db_session):
    """
    Test #531: Cannot delete branch from another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_del@test.com", status=UserStatus.verified)
    user2 = User(email="deleter@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    contact = Contact(owner_user_id=user1.id, first_name="Safe Branch")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Protected"))
    branch, _ = add_branch(db_session, user1.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    result = delete_branch(db_session, user2.id, folder.id, branch.id)

    # Assert
    assert result is False


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_delete_nonexistent_branch(db_session):
    """
    Test #532: Deleting non-existent branch returns False

    Edge case handling.
    """
    # Arrange
    user = User(email="ghost_del@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Ghost"))

    # Act
    result = delete_branch(db_session, user.id, folder.id, 99999)

    # Assert
    assert result is False


# ==============================================================================
# BRANCH STATUS TRANSITIONS (Tests 533-536)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_branch_pending_to_active_transition(db_session):
    """
    Test #533: Branch can transition from pending to active

    Normal workflow: pending -> accepted -> active.
    """
    # Arrange
    user = User(email="transition1@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Acceptor")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Transition"))
    branch, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    updated = update_branch(
        db_session, user.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.active, accepted_at=datetime.utcnow())
    )

    # Assert
    assert updated.status == AssignmentStatus.active
    assert updated.accepted_at is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_branch_pending_to_declined_transition(db_session):
    """
    Test #534: Branch can transition from pending to declined

    Contact rejected the assignment.
    """
    # Arrange
    user = User(email="transition2@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Rejecter")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Reject"))
    branch, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    updated = update_branch(
        db_session, user.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.declined)
    )

    # Assert
    assert updated.status == AssignmentStatus.declined


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_branch_active_to_removed_transition(db_session):
    """
    Test #535: Active branch can be removed

    User revokes branch assignment.
    """
    # Arrange
    user = User(email="transition3@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Removed")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Remove"))
    branch, _ = add_branch(
        db_session, user.id, folder.id,
        BranchCreate(contact_id=contact.id, status=AssignmentStatus.active)
    )

    # Act
    updated = update_branch(
        db_session, user.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.removed)
    )

    # Assert
    assert updated.status == AssignmentStatus.removed


@pytest.mark.unit
@pytest.mark.folders
def test_branch_accepted_at_timestamp(db_session):
    """
    Test #536: accepted_at timestamp set when branch becomes active

    Tracks when contact accepted the assignment.
    """
    # Arrange
    user = User(email="timestamp@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Timer")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Timestamp"))
    branch, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Act
    before = datetime.utcnow()
    updated = update_branch(
        db_session, user.id, folder.id, branch.id,
        BranchUpdate(status=AssignmentStatus.active, accepted_at=datetime.utcnow())
    )
    after = datetime.utcnow()

    # Assert
    assert updated.accepted_at is not None
    assert before <= updated.accepted_at <= after


# ==============================================================================
# UNIQUENESS CONSTRAINT TESTS (Tests 537-539)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_branch_unique_per_folder_contact_pair(db_session):
    """
    Test #537: Only one branch per (folder, contact) pair

    Database enforces uniqueness constraint.
    """
    # Arrange
    user = User(email="unique1@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Unique")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Unique"))

    # Act
    branch1, error1 = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))
    branch2, error2 = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id))

    # Assert
    assert branch1 is not None
    assert branch2 is None
    assert error2 == "branch_exists"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_same_contact_different_folders_allowed(db_session):
    """
    Test #538: Same contact can be branch in multiple folders

    Uniqueness is per folder, not global.
    """
    # Arrange
    user = User(email="multi_folder@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Multi")
    db_session.add(contact)
    db_session.commit()

    folder1 = create_folder(db_session, user.id, FolderCreate(name="Folder 1"))
    folder2 = create_folder(db_session, user.id, FolderCreate(name="Folder 2"))

    # Act
    branch1, _ = add_branch(db_session, user.id, folder1.id, BranchCreate(contact_id=contact.id))
    branch2, _ = add_branch(db_session, user.id, folder2.id, BranchCreate(contact_id=contact.id))

    # Assert
    assert branch1 is not None
    assert branch2 is not None
    assert branch1.folder_id != branch2.folder_id


@pytest.mark.unit
@pytest.mark.folders
def test_different_contacts_same_folder_allowed(db_session):
    """
    Test #539: Multiple different contacts can be branches in same folder

    One folder can have many branches.
    """
    # Arrange
    user = User(email="many_branches@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="First")
    contact2 = Contact(owner_user_id=user.id, first_name="Second")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Many"))

    # Act
    branch1, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact1.id))
    branch2, _ = add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact2.id))

    # Assert
    assert branch1 is not None
    assert branch2 is not None
    assert branch1.contact_id != branch2.contact_id
