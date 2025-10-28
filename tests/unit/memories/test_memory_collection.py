"""
Module 6: Memories - Memory Collection Tests (Tests 590-619)

Tests MemoryCollection model CRUD and business logic.

Test Categories:
- Create collection (Tests 590-594)
- Read collection (Tests 595-597)
- Update collection (Tests 598-601)
- Delete collection (Tests 602-604)
- Trigger configuration (Tests 605-609)
- Status management (Tests 610-614)
- Armed state (Tests 615-619)
"""
# Standard library
import pytest
from datetime import datetime, timedelta

# Application imports
from app.models.user import User, UserStatus
from app.models.memory import MemoryCollection
from app.models.enums import EventType, FolderStatus


# ==============================================================================
# CREATE COLLECTION TESTS (Tests 590-594)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_create_memory_collection_basic(db_session):
    """
    Test #590: Create memory collection with basic fields

    Verifies memory collection creation.
    """
    # Arrange
    user = User(email="memory@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(
        user_id=user.id,
        name="Birthday Memories",
        description="Photos and videos from my birthdays"
    )
    db_session.add(collection)
    db_session.commit()
    db_session.refresh(collection)

    # Assert
    assert collection.id is not None
    assert collection.user_id == user.id
    assert collection.name == "Birthday Memories"
    assert collection.description == "Photos and videos from my birthdays"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_create_memory_collection_default_event_type(db_session):
    """
    Test #591: Default event_type is 'event'

    Event-based is default trigger type.
    """
    # Arrange
    user = User(email="event_default@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(user_id=user.id, name="Default Event")
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.event_type == EventType.event


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_create_memory_collection_time_based(db_session):
    """
    Test #592: Create time-based memory collection

    Time-based trigger for scheduled release.
    """
    # Arrange
    user = User(email="time_memory@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    release_time = datetime(2030, 1, 1, 0, 0)

    # Act
    collection = MemoryCollection(
        user_id=user.id,
        name="Future Release",
        event_type=EventType.time,
        scheduled_at=release_time
    )
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.event_type == EventType.time
    assert collection.scheduled_at == release_time


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_create_memory_collection_event_based(db_session):
    """
    Test #593: Create event-based memory collection

    Event trigger with label.
    """
    # Arrange
    user = User(email="event_memory@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(
        user_id=user.id,
        name="After Death",
        event_type=EventType.event,
        event_label="death_declaration"
    )
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.event_type == EventType.event
    assert collection.event_label == "death_declaration"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_create_memory_collection_defaults_incomplete(db_session):
    """
    Test #594: New collection defaults to incomplete status

    Collections start incomplete until armed.
    """
    # Arrange
    user = User(email="status_default@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(user_id=user.id, name="Incomplete")
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.status == FolderStatus.incomplete
    assert collection.is_armed is False


# ==============================================================================
# READ COLLECTION TESTS (Tests 595-597)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_get_user_memory_collections(db_session):
    """
    Test #595: Retrieve all memory collections for a user

    Verifies collection listing.
    """
    # Arrange
    user = User(email="list_mem@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection1 = MemoryCollection(user_id=user.id, name="Collection 1")
    collection2 = MemoryCollection(user_id=user.id, name="Collection 2")
    db_session.add_all([collection1, collection2])
    db_session.commit()

    # Act
    collections = db_session.query(MemoryCollection).filter(MemoryCollection.user_id == user.id).all()

    # Assert
    assert len(collections) == 2
    names = {c.name for c in collections}
    assert "Collection 1" in names
    assert "Collection 2" in names


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_get_memory_collection_by_id(db_session):
    """
    Test #596: Retrieve specific memory collection by ID

    Verifies single collection retrieval.
    """
    # Arrange
    user = User(email="get_one@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Target")
    db_session.add(collection)
    db_session.commit()

    # Act
    result = db_session.query(MemoryCollection).filter(MemoryCollection.id == collection.id).first()

    # Assert
    assert result is not None
    assert result.id == collection.id
    assert result.name == "Target"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_get_memory_collection_user_isolation(db_session):
    """
    Test #597: Users cannot access other users' collections

    CRITICAL: Multi-tenant data isolation.
    """
    # Arrange
    user1 = User(email="user1_mem@test.com", status=UserStatus.verified)
    user2 = User(email="user2_mem@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    collection = MemoryCollection(user_id=user1.id, name="Private")
    db_session.add(collection)
    db_session.commit()

    # Act
    result = db_session.query(MemoryCollection).filter(
        MemoryCollection.id == collection.id,
        MemoryCollection.user_id == user2.id
    ).first()

    # Assert
    assert result is None  # user2 cannot see user1's collection


# ==============================================================================
# UPDATE COLLECTION TESTS (Tests 598-601)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_update_memory_collection_name(db_session):
    """
    Test #598: Update memory collection name

    Verifies collection renaming.
    """
    # Arrange
    user = User(email="update_mem@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Old Name")
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.name = "New Name"
    db_session.commit()
    db_session.refresh(collection)

    # Assert
    assert collection.name == "New Name"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_update_memory_collection_description(db_session):
    """
    Test #599: Update memory collection description

    Verifies description updates.
    """
    # Arrange
    user = User(email="update_desc@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Test", description="Old")
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.description = "New description"
    db_session.commit()

    # Assert
    assert collection.description == "New description"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_update_memory_collection_trigger_time_to_event(db_session):
    """
    Test #600: Switch collection from time-based to event-based

    Allows changing trigger type.
    """
    # Arrange
    user = User(email="switch_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(
        user_id=user.id,
        name="Switch",
        event_type=EventType.time,
        scheduled_at=datetime(2025, 12, 31)
    )
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.event_type = EventType.event
    collection.event_label = "death"
    collection.scheduled_at = None
    db_session.commit()

    # Assert
    assert collection.event_type == EventType.event
    assert collection.event_label == "death"
    assert collection.scheduled_at is None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_update_memory_collection_timestamps(db_session):
    """
    Test #601: updated_at timestamp updates on modification

    Verifies automatic timestamp tracking.
    """
    # Arrange
    user = User(email="timestamps_mem@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Timestamp Test")
    db_session.add(collection)
    db_session.commit()

    original_updated_at = collection.updated_at

    # Act
    collection.name = "Updated Name"
    db_session.commit()
    db_session.refresh(collection)

    # Assert
    assert collection.updated_at > original_updated_at


# ==============================================================================
# DELETE COLLECTION TESTS (Tests 602-604)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_memory_collection(db_session):
    """
    Test #602: Delete memory collection

    Verifies collection deletion.
    """
    # Arrange
    user = User(email="delete_mem@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="To Delete")
    db_session.add(collection)
    db_session.commit()

    collection_id = collection.id

    # Act
    db_session.delete(collection)
    db_session.commit()

    # Assert
    result = db_session.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()
    assert result is None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_memory_collection_cascades_to_files(db_session):
    """
    Test #603: Deleting collection cascades to memory files

    CRITICAL: Cascade delete prevents orphaned files.
    """
    # Arrange
    from app.models.memory import MemoryFile

    user = User(email="cascade_mem@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Cascade Test")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/file.jpg", title="File")
    db_session.add(file)
    db_session.commit()

    file_id = file.id

    # Act
    db_session.delete(collection)
    db_session.commit()

    # Assert
    deleted_file = db_session.query(MemoryFile).filter(MemoryFile.id == file_id).first()
    assert deleted_file is None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_memory_collection_cascades_to_assignments(db_session):
    """
    Test #604: Deleting collection cascades to collection assignments

    CRITICAL: Cascade delete prevents orphaned assignments.
    """
    # Arrange
    from app.models.memory import MemoryCollectionAssignment
    from app.models.contact import Contact
    from app.models.enums import AssignmentRole

    user = User(email="cascade_assign@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    contact = Contact(owner_user_id=user.id, first_name="Test")
    db_session.add(contact)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Cascade Assign")
    db_session.add(collection)
    db_session.commit()

    assignment = MemoryCollectionAssignment(
        collection_id=collection.id,
        contact_id=contact.id,
        role=AssignmentRole.branch
    )
    db_session.add(assignment)
    db_session.commit()

    assignment_id = assignment.id

    # Act
    db_session.delete(collection)
    db_session.commit()

    # Assert
    deleted_assignment = db_session.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.id == assignment_id
    ).first()
    assert deleted_assignment is None


# ==============================================================================
# TRIGGER CONFIGURATION TESTS (Tests 605-609)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_time_trigger_requires_scheduled_at(db_session):
    """
    Test #605: Time-based trigger should have scheduled_at

    Validates required fields for time triggers.
    """
    # Arrange
    user = User(email="time_req@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(
        user_id=user.id,
        name="Time Required",
        event_type=EventType.time,
        scheduled_at=datetime(2030, 1, 1)
    )
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.scheduled_at is not None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_event_trigger_has_event_label(db_session):
    """
    Test #606: Event-based trigger should have event_label

    Validates event label configuration.
    """
    # Arrange
    user = User(email="event_label@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(
        user_id=user.id,
        name="Event Label",
        event_type=EventType.event,
        event_label="incapacitation"
    )
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.event_label is not None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_reschedule_time_trigger(db_session):
    """
    Test #607: Can reschedule time-based trigger

    Allows updating scheduled_at.
    """
    # Arrange
    user = User(email="reschedule_mem@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    old_time = datetime(2025, 6, 1)
    new_time = datetime(2026, 6, 1)

    collection = MemoryCollection(
        user_id=user.id,
        name="Reschedule",
        event_type=EventType.time,
        scheduled_at=old_time
    )
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.scheduled_at = new_time
    db_session.commit()

    # Assert
    assert collection.scheduled_at == new_time


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_change_event_label(db_session):
    """
    Test #608: Can change event label

    Allows updating event trigger.
    """
    # Arrange
    user = User(email="change_event@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(
        user_id=user.id,
        name="Change Event",
        event_type=EventType.event,
        event_label="death"
    )
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.event_label = "incapacitation"
    db_session.commit()

    # Assert
    assert collection.event_label == "incapacitation"


@pytest.mark.unit
@pytest.mark.memories
def test_future_scheduled_at_valid(db_session):
    """
    Test #609: scheduled_at can be in the future

    Validates future datetime scheduling.
    """
    # Arrange
    user = User(email="future@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    future_time = datetime.utcnow() + timedelta(days=365)

    # Act
    collection = MemoryCollection(
        user_id=user.id,
        name="Future",
        event_type=EventType.time,
        scheduled_at=future_time
    )
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.scheduled_at > datetime.utcnow()


# ==============================================================================
# STATUS MANAGEMENT TESTS (Tests 610-614)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_collection_status_defaults_incomplete(db_session):
    """
    Test #610: Collection status defaults to incomplete

    New collections start incomplete.
    """
    # Arrange
    user = User(email="status_incomplete@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(user_id=user.id, name="Status Test")
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.status == FolderStatus.incomplete


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_update_collection_status_to_complete(db_session):
    """
    Test #611: Can update collection status to complete

    Status transitions to complete when requirements met.
    """
    # Arrange
    user = User(email="status_complete@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Complete")
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.status = FolderStatus.complete
    db_session.commit()

    # Assert
    assert collection.status == FolderStatus.complete


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_collection_status_field_exists(db_session):
    """
    Test #612: Collection has status field

    Verifies status column exists.
    """
    # Arrange
    user = User(email="has_status@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Status Field")
    db_session.add(collection)
    db_session.commit()

    # Act & Assert
    assert hasattr(collection, 'status')
    assert collection.status in [FolderStatus.incomplete, FolderStatus.complete]


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_collection_status_persists(db_session):
    """
    Test #613: Status persists across sessions

    Validates status is stored in database.
    """
    # Arrange
    user = User(email="persist_status@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Persist")
    collection.status = FolderStatus.complete
    db_session.add(collection)
    db_session.commit()

    collection_id = collection.id

    # Act - Reload from database
    db_session.expire_all()
    reloaded = db_session.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()

    # Assert
    assert reloaded.status == FolderStatus.complete


@pytest.mark.unit
@pytest.mark.memories
def test_collection_created_at_set(db_session):
    """
    Test #614: created_at timestamp set automatically

    Validates automatic timestamp generation.
    """
    # Arrange
    user = User(email="created_at@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    before = datetime.utcnow()
    collection = MemoryCollection(user_id=user.id, name="Timestamp")
    db_session.add(collection)
    db_session.commit()
    after = datetime.utcnow()

    # Assert
    assert collection.created_at is not None
    assert before <= collection.created_at <= after


# ==============================================================================
# ARMED STATE TESTS (Tests 615-619)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_collection_armed_defaults_false(db_session):
    """
    Test #615: is_armed defaults to False

    Collections start unarmed.
    """
    # Arrange
    user = User(email="unarmed@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    collection = MemoryCollection(user_id=user.id, name="Unarmed")
    db_session.add(collection)
    db_session.commit()

    # Assert
    assert collection.is_armed is False


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_arm_memory_collection(db_session):
    """
    Test #616: Can arm memory collection

    Arming activates collection for release.
    """
    # Arrange
    user = User(email="arm@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Arm Test")
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.is_armed = True
    db_session.commit()

    # Assert
    assert collection.is_armed is True


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_disarm_memory_collection(db_session):
    """
    Test #617: Can disarm armed collection

    Allows deactivating collection.
    """
    # Arrange
    user = User(email="disarm@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Disarm Test", is_armed=True)
    db_session.add(collection)
    db_session.commit()

    # Act
    collection.is_armed = False
    db_session.commit()

    # Assert
    assert collection.is_armed is False


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_armed_collection_persists(db_session):
    """
    Test #618: Armed state persists across sessions

    Validates is_armed is stored in database.
    """
    # Arrange
    user = User(email="persist_armed@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Persist Armed", is_armed=True)
    db_session.add(collection)
    db_session.commit()

    collection_id = collection.id

    # Act - Reload from database
    db_session.expire_all()
    reloaded = db_session.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()

    # Assert
    assert reloaded.is_armed is True


@pytest.mark.unit
@pytest.mark.memories
def test_multiple_users_independent_collections(db_session):
    """
    Test #619: Different users have independent collections

    Validates multi-tenant isolation.
    """
    # Arrange
    user1 = User(email="user1_independent@test.com", status=UserStatus.verified)
    user2 = User(email="user2_independent@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    # Act
    collection1 = MemoryCollection(user_id=user1.id, name="User 1 Collection")
    collection2 = MemoryCollection(user_id=user2.id, name="User 2 Collection")
    db_session.add_all([collection1, collection2])
    db_session.commit()

    user1_collections = db_session.query(MemoryCollection).filter(MemoryCollection.user_id == user1.id).all()
    user2_collections = db_session.query(MemoryCollection).filter(MemoryCollection.user_id == user2.id).all()

    # Assert
    assert len(user1_collections) == 1
    assert len(user2_collections) == 1
    assert user1_collections[0].id != user2_collections[0].id
