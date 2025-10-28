"""
Module 5: Folders - Status Computation Tests (Tests 580-589)

Tests folder status computation logic (complete/incomplete).

Test Categories:
- Status computation rules (Tests 580-584)
- Missing requirements (Tests 585-589)
"""
# Standard library
import pytest
from datetime import datetime

# Application imports
from controller.folder import (
    create_folder,
    get_folder,
    add_branch,
    add_leaf,
    upsert_trigger,
    _compute_status_and_missing
)
from app.models.user import User, UserStatus
from app.models.contact import Contact
from app.models.folder import AssignmentStatus, TriggerType, TriggerState
from app.schemas.folder import FolderCreate, BranchCreate, LeafCreate, TriggerUpsert, FolderComputedStatus


# ==============================================================================
# STATUS COMPUTATION RULES (Tests 580-584)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_status_incomplete_no_assignments(db_session):
    """
    Test #580: Folder is incomplete without branches/leaves/trigger

    New folder starts as incomplete.
    """
    # Arrange
    user = User(email="status1@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Empty"))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert "active branch" in missing
    assert "active leaf" in missing
    assert "trigger" in missing


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_status_complete_all_requirements(db_session):
    """
    Test #581: Folder is complete with branch + leaf + trigger

    CRITICAL: Completeness requirements validation.
    """
    # Arrange
    user = User(email="complete@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Complete")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Complete"))

    # Add branch (active)
    add_branch(
        db_session, user.id, folder.id,
        BranchCreate(contact_id=contact.id, status=AssignmentStatus.active)
    )

    # Add leaf (active)
    add_leaf(
        db_session, user.id, folder.id,
        LeafCreate(contact_id=contact.id, status=AssignmentStatus.active)
    )

    # Add trigger
    upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="death")
    )

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.complete
    assert missing is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_status_pending_branch_counts_as_active(db_session):
    """
    Test #582: Pending branch counts toward completeness

    Pending assignments still count (not yet declined).
    """
    # Arrange
    user = User(email="pending@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Pending")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Pending"))

    # Add pending branch
    add_branch(
        db_session, user.id, folder.id,
        BranchCreate(contact_id=contact.id, status=AssignmentStatus.pending)
    )

    # Add active leaf
    add_leaf(
        db_session, user.id, folder.id,
        LeafCreate(contact_id=contact.id, status=AssignmentStatus.active)
    )

    # Add trigger
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.event_based, event_label="death"))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.complete


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_status_declined_branch_not_counted(db_session):
    """
    Test #583: Declined branch doesn't count toward completeness

    CRITICAL: Declined/removed assignments excluded.
    """
    # Arrange
    user = User(email="declined@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Declined")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Declined"))

    # Add declined branch
    add_branch(
        db_session, user.id, folder.id,
        BranchCreate(contact_id=contact.id, status=AssignmentStatus.declined)
    )

    # Add active leaf
    add_leaf(
        db_session, user.id, folder.id,
        LeafCreate(contact_id=contact.id, status=AssignmentStatus.active)
    )

    # Add trigger
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.event_based, event_label="death"))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert "active branch" in missing


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_status_cancelled_trigger_not_counted(db_session):
    """
    Test #584: Cancelled trigger makes folder incomplete

    CRITICAL: Cancelled triggers excluded from count.
    """
    # Arrange
    user = User(email="cancelled_trig@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Contact")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Cancelled"))

    # Add active branch and leaf
    add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id, status=AssignmentStatus.active))
    add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, status=AssignmentStatus.active))

    # Add cancelled trigger
    upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="death", state=TriggerState.cancelled)
    )

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert "trigger" in missing


# ==============================================================================
# MISSING REQUIREMENTS TESTS (Tests 585-589)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_missing_only_branch(db_session):
    """
    Test #585: Missing requirements shows only branch needed

    Folder has leaf and trigger but no branch.
    """
    # Arrange
    user = User(email="no_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="No Branch")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="No Branch"))

    # Add leaf and trigger only
    add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, status=AssignmentStatus.active))
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.event_based, event_label="death"))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert missing == "active branch"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_missing_only_leaf(db_session):
    """
    Test #586: Missing requirements shows only leaf needed

    Folder has branch and trigger but no leaf.
    """
    # Arrange
    user = User(email="no_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="No Leaf")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="No Leaf"))

    # Add branch and trigger only
    add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id, status=AssignmentStatus.active))
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.event_based, event_label="death"))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert missing == "active leaf"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_missing_only_trigger(db_session):
    """
    Test #587: Missing requirements shows only trigger needed

    Folder has branch and leaf but no trigger.
    """
    # Arrange
    user = User(email="no_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="No Trigger")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="No Trigger"))

    # Add branch and leaf only
    add_branch(db_session, user.id, folder.id, BranchCreate(contact_id=contact.id, status=AssignmentStatus.active))
    add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, status=AssignmentStatus.active))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert missing == "exactly 1 (non-cancelled) trigger"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_folder_missing_multiple_requirements(db_session):
    """
    Test #588: Missing requirements shows all missing items

    Folder missing multiple requirements.
    """
    # Arrange
    user = User(email="missing_multi@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Multi Missing")
    db_session.add(contact)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Missing"))

    # Add only leaf (missing branch and trigger)
    add_leaf(db_session, user.id, folder.id, LeafCreate(contact_id=contact.id, status=AssignmentStatus.active))

    # Act
    status, missing = _compute_status_and_missing(db_session, folder.id)

    # Assert
    assert status == FolderComputedStatus.incomplete
    assert "active branch" in missing
    assert "trigger" in missing


@pytest.mark.unit
@pytest.mark.folders
def test_get_folder_includes_status(db_session):
    """
    Test #589: get_folder returns status and missing fields

    Folder response includes computed status.
    """
    # Arrange
    user = User(email="status_resp@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Status Response"))

    # Act
    folder_dict = get_folder(db_session, user.id, folder.id)

    # Assert
    assert "status" in folder_dict
    assert "missing" in folder_dict
    assert folder_dict["status"] == FolderComputedStatus.incomplete
    assert folder_dict["missing"] is not None
