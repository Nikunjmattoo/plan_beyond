"""
Module 6: Memories - Assignment Tests (Tests 645-664)

Tests MemoryCollectionAssignment for branch/leaf roles.

Test Categories:
- Add assignments (Tests 645-649)
- Branch invites (Tests 650-654)
- Delete assignments (Tests 655-657)
- Role validation (Tests 658-661)
- Uniqueness constraints (Tests 662-664)
"""
# Standard library
import pytest
from datetime import datetime

# Third-party
from sqlalchemy.exc import IntegrityError

# Application imports
from app.models.user import User, UserStatus
from app.models.memory import MemoryCollection, MemoryCollectionAssignment
from app.models.contact import Contact
from app.models.enums import AssignmentRole, BranchInviteStatus


# ==============================================================================
# ADD ASSIGNMENTS TESTS (Tests 645-649)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_add_branch_assignment(db_session):
    """
    Test #645: Add branch assignment to collection

    Branch role for viewing/managing.
    """
    # Arrange
    user = User(email="branch_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Branch Contact")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Branch Test")
    db_session.add(collection)
    db_session.commit()

    # Act
    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch
    )
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.id is not None
    assert assignment.role == AssignmentRole.branch


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_add_leaf_assignment(db_session):
    """
    Test #646: Add leaf assignment to collection

    Leaf role for receiving memories.
    """
    # Arrange
    user = User(email="leaf_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Leaf Contact")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Leaf Test")
    db_session.add(collection)
    db_session.commit()

    # Act
    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.leaf
    )
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.role == AssignmentRole.leaf


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_add_multiple_assignments(db_session):
    """
    Test #647: Collection can have multiple assignments

    Multiple branch and leaf assignments.
    """
    # Arrange
    user = User(email="multi_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Contact 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Contact 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Multi Assign")
    db_session.add(collection)
    db_session.commit()

    # Act
    assign1 = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact1.id, role=AssignmentRole.branch)
    assign2 = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact2.id, role=AssignmentRole.leaf)
    db_session.add_all([assign1, assign2])
    db_session.commit()

    # Assert
    assignments = db_session.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.collection_id == collection.id
    ).all()
    assert len(assignments) == 2


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_same_contact_different_roles_allowed(db_session):
    """
    Test #648: Same contact can have both branch and leaf roles

    Role differentiation allowed.
    """
    # Arrange
    user = User(email="both_roles@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Both Roles")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Both Roles")
    db_session.add(collection)
    db_session.commit()

    # Act
    branch = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    leaf = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.leaf)
    db_session.add_all([branch, leaf])
    db_session.commit()

    # Assert
    assert branch.id != leaf.id


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_assignment_cascade_on_collection_delete(db_session):
    """
    Test #649: Assignments deleted when collection deleted

    CASCADE delete verified.
    """
    # Arrange
    user = User(email="cascade_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Cascade")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Cascade")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assignment)
    db_session.commit()

    assignment_id = assignment.id

    # Act
    db_session.delete(collection)
    db_session.commit()

    # Assert
    deleted = db_session.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.id == assignment_id
    ).first()
    assert deleted is None


# ==============================================================================
# BRANCH INVITE TESTS (Tests 650-654)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_branch_invite_status_field(db_session):
    """
    Test #650: Branch assignments have invite_status field

    Invite lifecycle tracking.
    """
    # Arrange
    user = User(email="invite_status@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Invite")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Invite")
    db_session.add(collection)
    db_session.commit()

    # Act
    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch,
        invite_status=BranchInviteStatus.sent
    )
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.invite_status == BranchInviteStatus.sent


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_branch_invite_accepted_status(db_session):
    """
    Test #651: Branch invite can be accepted

    Status transition to accepted.
    """
    # Arrange
    user = User(email="accepted@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Accepted")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Accepted")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch,
        invite_status=BranchInviteStatus.sent
    )
    db_session.add(assignment)
    db_session.commit()

    # Act
    assignment.invite_status = BranchInviteStatus.accepted
    assignment.responded_at = datetime.utcnow()
    db_session.commit()

    # Assert
    assert assignment.invite_status == BranchInviteStatus.accepted
    assert assignment.responded_at is not None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_branch_invite_declined_status(db_session):
    """
    Test #652: Branch invite can be declined

    Status transition to declined.
    """
    # Arrange
    user = User(email="declined@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Declined")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Declined")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch,
        invite_status=BranchInviteStatus.sent
    )
    db_session.add(assignment)
    db_session.commit()

    # Act
    assignment.invite_status = BranchInviteStatus.declined
    assignment.responded_at = datetime.utcnow()
    db_session.commit()

    # Assert
    assert assignment.invite_status == BranchInviteStatus.declined


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_branch_invite_timestamps(db_session):
    """
    Test #653: Branch invite has invited_at and responded_at timestamps

    Tracks invite lifecycle timing.
    """
    # Arrange
    user = User(email="timestamps@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Timestamps")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Timestamps")
    db_session.add(collection)
    db_session.commit()

    # Act
    invited_time = datetime.utcnow()
    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch,
        invite_status=BranchInviteStatus.sent,
        invited_at=invited_time
    )
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.invited_at == invited_time


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_branch_invite_token_field(db_session):
    """
    Test #654: Branch invite has token field for public accept/decline

    Token for URL-based responses.
    """
    # Arrange
    user = User(email="token@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Token")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Token")
    db_session.add(collection)
    db_session.commit()

    # Act
    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch,
        invite_token="abc123def456",
        invite_expires_at=datetime.utcnow()
    )
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.invite_token == "abc123def456"
    assert assignment.invite_expires_at is not None


# ==============================================================================
# DELETE ASSIGNMENTS TESTS (Tests 655-657)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_assignment(db_session):
    """
    Test #655: Delete collection assignment

    Verifies assignment removal.
    """
    # Arrange
    user = User(email="del_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Delete")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Delete")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assignment)
    db_session.commit()

    assignment_id = assignment.id

    # Act
    db_session.delete(assignment)
    db_session.commit()

    # Assert
    deleted = db_session.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.id == assignment_id
    ).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_assignment_preserves_collection(db_session):
    """
    Test #656: Deleting assignment doesn't delete collection

    Assignments removable independently.
    """
    # Arrange
    user = User(email="keep_coll@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Keep")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Keep")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assignment)
    db_session.commit()

    # Act
    db_session.delete(assignment)
    db_session.commit()

    # Assert
    still_exists = db_session.query(MemoryCollection).filter(MemoryCollection.id == collection.id).first()
    assert still_exists is not None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_assignment_on_contact_deletion(db_session):
    """
    Test #657: Assignments deleted when contact deleted

    CASCADE on contact foreign key.
    """
    # Arrange
    user = User(email="cascade_contact@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Cascade Contact")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Cascade")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assignment)
    db_session.commit()

    assignment_id = assignment.id

    # Act
    db_session.delete(contact)
    db_session.commit()

    # Assert
    deleted = db_session.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.id == assignment_id
    ).first()
    assert deleted is None


# ==============================================================================
# ROLE VALIDATION TESTS (Tests 658-661)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_assignment_role_required(db_session):
    """
    Test #658: Assignment must have role (NOT NULL)

    Role is mandatory field.
    """
    # Arrange
    user = User(email="role_req@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Role")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Role")
    db_session.add(collection)
    db_session.commit()

    # Act & Assert
    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=None)
    db_session.add(assignment)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_assignment_role_branch_valid(db_session):
    """
    Test #659: branch is valid role

    Branch role accepted.
    """
    # Arrange
    user = User(email="role_branch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Branch")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Branch")
    db_session.add(collection)
    db_session.commit()

    # Act
    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.role == AssignmentRole.branch


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_assignment_role_leaf_valid(db_session):
    """
    Test #660: leaf is valid role

    Leaf role accepted.
    """
    # Arrange
    user = User(email="role_leaf@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Leaf")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Leaf")
    db_session.add(collection)
    db_session.commit()

    # Act
    assignment = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.leaf)
    db_session.add(assignment)
    db_session.commit()

    # Assert
    assert assignment.role == AssignmentRole.leaf


@pytest.mark.unit
@pytest.mark.memories
def test_collection_has_assignments_relationship(db_session):
    """
    Test #661: Collection has folder_assignments relationship

    Relationship configured.
    """
    # Arrange
    user = User(email="rel@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Relationship")
    db_session.add(collection)
    db_session.commit()

    db_session.refresh(collection)

    # Act & Assert
    assert hasattr(collection, 'folder_assignments')


# ==============================================================================
# UNIQUENESS CONSTRAINT TESTS (Tests 662-664)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_duplicate_assignment_same_role_fails(db_session):
    """
    Test #662: Cannot add same (collection, contact, role) twice

    CRITICAL: Uniqueness constraint enforced.
    """
    # Arrange
    user = User(email="dup_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Dup")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Dup")
    db_session.add(collection)
    db_session.commit()

    assign1 = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assign1)
    db_session.commit()

    # Act & Assert
    assign2 = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add(assign2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_same_contact_multiple_collections(db_session):
    """
    Test #663: Same contact can be assigned to multiple collections

    Uniqueness is per collection.
    """
    # Arrange
    user = User(email="multi_coll@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Multi")
    db_session.add(contact)
    db_session.commit()

    coll1 = MemoryCollection(user_id=user.id, name="Collection 1")
    coll2 = MemoryCollection(user_id=user.id, name="Collection 2")
    db_session.add_all([coll1, coll2])
    db_session.commit()

    # Act
    assign1 = MemoryCollectionAssignment(collection_id=coll1.id, contact_id=contact.id, role=AssignmentRole.branch)
    assign2 = MemoryCollectionAssignment(collection_id=coll2.id, contact_id=contact.id, role=AssignmentRole.branch)
    db_session.add_all([assign1, assign2])
    db_session.commit()

    # Assert
    assert assign1.id != assign2.id


@pytest.mark.unit
@pytest.mark.memories
def test_different_contacts_same_collection(db_session):
    """
    Test #664: Multiple contacts can be assigned to same collection

    One collection, many assignments.
    """
    # Arrange
    user = User(email="many_contacts@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact1 = Contact(owner_user_id=user.id, first_name="Contact 1")
    contact2 = Contact(owner_user_id=user.id, first_name="Contact 2")
    db_session.add_all([contact1, contact2])
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Many")
    db_session.add(collection)
    db_session.commit()

    # Act
    assign1 = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact1.id, role=AssignmentRole.branch)
    assign2 = MemoryCollectionAssignment(collection_id=collection.id, contact_id=contact2.id, role=AssignmentRole.leaf)
    db_session.add_all([assign1, assign2])
    db_session.commit()

    # Assert
    assignments = db_session.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.collection_id == collection.id
    ).all()
    assert len(assignments) == 2
