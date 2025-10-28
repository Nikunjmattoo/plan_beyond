"""
Module 5: Folders - Trigger Controller Tests (Tests 560-579)

Tests trigger management for folders (time-based and event-based).

Test Categories:
- Upsert trigger (Tests 560-564)
- Get trigger (Tests 565-566)
- Time-based triggers (Tests 567-570)
- Event-based triggers (Tests 571-574)
- Trigger states (Tests 575-579)
"""
# Standard library
import pytest
from datetime import datetime, timedelta

# Application imports
from controller.folder import (
    create_folder,
    upsert_trigger,
    get_trigger
)
from app.models.user import User, UserStatus
from app.models.folder import TriggerType, TriggerState
from app.schemas.folder import FolderCreate, TriggerUpsert


# ==============================================================================
# UPSERT TRIGGER TESTS (Tests 560-564)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_upsert_trigger_creates_new(db_session):
    """
    Test #560: Upsert creates trigger if none exists

    First call creates new trigger.
    """
    # Arrange
    user = User(email="trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Trigger Test"))

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=datetime(2025, 12, 31, 23, 59), timezone="UTC")
    )

    # Assert
    assert trigger is not None
    assert trigger.folder_id == folder.id
    assert trigger.type == TriggerType.time_based
    assert trigger.state == TriggerState.configured


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_upsert_trigger_updates_existing(db_session):
    """
    Test #561: Upsert updates trigger if already exists

    CRITICAL: Only one trigger per folder (singleton constraint).
    """
    # Arrange
    user = User(email="upsert@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Upsert"))

    # First upsert
    trigger1 = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=datetime(2025, 6, 1), timezone="UTC")
    )

    # Act - Second upsert
    trigger2 = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="death_declaration")
    )

    # Assert
    assert trigger1.id == trigger2.id  # Same trigger updated
    assert trigger2.type == TriggerType.event_based


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_upsert_trigger_wrong_user_fails(db_session):
    """
    Test #562: Cannot upsert trigger for another user's folder

    CRITICAL: Authorization check.
    """
    # Arrange
    user1 = User(email="owner_trigger@test.com", status=UserStatus.verified)
    user2 = User(email="hacker_trigger@test.com", status=UserStatus.verified)
    db_session.add_all([user1, user2])
    db_session.commit()

    folder = create_folder(db_session, user1.id, FolderCreate(name="Private"))

    # Act
    trigger = upsert_trigger(
        db_session, user2.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based)
    )

    # Assert
    assert trigger is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_upsert_trigger_nonexistent_folder(db_session):
    """
    Test #563: Upsert trigger for non-existent folder returns None

    Edge case handling.
    """
    # Arrange
    user = User(email="ghost_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    # Act
    trigger = upsert_trigger(
        db_session, user.id, 99999,
        TriggerUpsert(type=TriggerType.time_based)
    )

    # Assert
    assert trigger is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_only_one_trigger_per_folder(db_session):
    """
    Test #564: Folder can have exactly one trigger (singleton)

    CRITICAL: Uniqueness constraint enforced.
    """
    # Arrange
    from app.models.folder import FolderTrigger

    user = User(email="singleton@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Singleton"))

    # Act
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based))
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.event_based))

    # Assert - Only one trigger should exist
    triggers = db_session.query(FolderTrigger).filter(FolderTrigger.folder_id == folder.id).all()
    assert len(triggers) == 1


# ==============================================================================
# GET TRIGGER TESTS (Tests 565-566)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_get_trigger_returns_trigger(db_session):
    """
    Test #565: get_trigger returns folder's trigger

    Verifies trigger retrieval.
    """
    # Arrange
    user = User(email="get_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Get"))
    created = upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based))

    # Act
    trigger = get_trigger(db_session, user.id, folder.id)

    # Assert
    assert trigger is not None
    assert trigger.id == created.id


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_get_trigger_none_if_no_trigger(db_session):
    """
    Test #566: get_trigger returns None if folder has no trigger

    Edge case: folder without trigger.
    """
    # Arrange
    user = User(email="no_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="No Trigger"))

    # Act
    trigger = get_trigger(db_session, user.id, folder.id)

    # Assert
    assert trigger is None


# ==============================================================================
# TIME-BASED TRIGGER TESTS (Tests 567-570)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_time_based_trigger(db_session):
    """
    Test #567: Create time-based trigger with specific datetime

    Time-based triggers fire at specific time.
    """
    # Arrange
    user = User(email="time_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Time"))
    release_time = datetime(2030, 1, 1, 0, 0)

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=release_time, timezone="America/New_York")
    )

    # Assert
    assert trigger.type == TriggerType.time_based
    assert trigger.time_at == release_time
    assert trigger.timezone == "America/New_York"
    assert trigger.event_label is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_time_based_trigger_requires_time_at(db_session):
    """
    Test #568: Time-based trigger should have time_at field

    Validates required fields for time-based triggers.
    """
    # Arrange
    user = User(email="time_req@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Time Req"))

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=datetime(2025, 12, 31), timezone="UTC")
    )

    # Assert
    assert trigger.time_at is not None
    assert trigger.timezone is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_time_based_trigger_datetime(db_session):
    """
    Test #569: Update time-based trigger to different datetime

    Allows rescheduling trigger.
    """
    # Arrange
    user = User(email="reschedule@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Reschedule"))

    old_time = datetime(2025, 6, 1)
    new_time = datetime(2026, 6, 1)

    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based, time_at=old_time, timezone="UTC"))

    # Act
    updated = upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based, time_at=new_time, timezone="UTC"))

    # Assert
    assert updated.time_at == new_time


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_time_based_trigger_timezone_support(db_session):
    """
    Test #570: Time-based trigger stores timezone

    CRITICAL: Timezone support for international users.
    """
    # Arrange
    user = User(email="timezone@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Timezone"))

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(
            type=TriggerType.time_based,
            time_at=datetime(2025, 12, 31, 23, 59),
            timezone="Asia/Kolkata"
        )
    )

    # Assert
    assert trigger.timezone == "Asia/Kolkata"


# ==============================================================================
# EVENT-BASED TRIGGER TESTS (Tests 571-574)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_create_event_based_trigger(db_session):
    """
    Test #571: Create event-based trigger with event label

    Event-based triggers fire on specific events (like death).
    """
    # Arrange
    user = User(email="event_trigger@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Event"))

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="death_declaration")
    )

    # Assert
    assert trigger.type == TriggerType.event_based
    assert trigger.event_label == "death_declaration"
    assert trigger.time_at is None
    assert trigger.timezone is None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_event_based_trigger_requires_event_label(db_session):
    """
    Test #572: Event-based trigger should have event_label

    Validates required fields for event-based triggers.
    """
    # Arrange
    user = User(email="event_req@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Event Req"))

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="user_incapacitation")
    )

    # Assert
    assert trigger.event_label is not None


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_switch_trigger_type_time_to_event(db_session):
    """
    Test #573: Can switch trigger from time-based to event-based

    Upsert allows changing trigger type.
    """
    # Arrange
    user = User(email="switch@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Switch"))

    # Start with time-based
    upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=datetime(2025, 12, 31), timezone="UTC")
    )

    # Act - Switch to event-based
    updated = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="death_declaration")
    )

    # Assert
    assert updated.type == TriggerType.event_based
    assert updated.event_label == "death_declaration"


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_switch_trigger_type_event_to_time(db_session):
    """
    Test #574: Can switch trigger from event-based to time-based

    Upsert allows changing trigger type bidirectionally.
    """
    # Arrange
    user = User(email="switch2@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Switch2"))

    # Start with event-based
    upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="incapacitation")
    )

    # Act - Switch to time-based
    new_time = datetime(2030, 1, 1)
    updated = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=new_time, timezone="UTC")
    )

    # Assert
    assert updated.type == TriggerType.time_based
    assert updated.time_at == new_time


# ==============================================================================
# TRIGGER STATE TESTS (Tests 575-579)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_trigger_default_state_configured(db_session):
    """
    Test #575: New trigger defaults to 'configured' state

    Initial state is configured (not yet scheduled).
    """
    # Arrange
    user = User(email="state@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="State"))

    # Act
    trigger = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, time_at=datetime(2025, 12, 31), timezone="UTC")
    )

    # Assert
    assert trigger.state == TriggerState.configured


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_trigger_state_to_scheduled(db_session):
    """
    Test #576: Can update trigger state to 'scheduled'

    When system scheduler picks up trigger.
    """
    # Arrange
    user = User(email="scheduled@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Scheduled"))
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based))

    # Act
    updated = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, state=TriggerState.scheduled)
    )

    # Assert
    assert updated.state == TriggerState.scheduled


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_trigger_state_to_fired(db_session):
    """
    Test #577: Can update trigger state to 'fired'

    When trigger has executed.
    """
    # Arrange
    user = User(email="fired@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Fired"))
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.event_based, event_label="death"))

    # Act
    updated = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.event_based, event_label="death", state=TriggerState.fired)
    )

    # Assert
    assert updated.state == TriggerState.fired


@pytest.mark.unit
@pytest.mark.folders
@pytest.mark.critical
def test_update_trigger_state_to_cancelled(db_session):
    """
    Test #578: Can update trigger state to 'cancelled'

    User cancels trigger.
    """
    # Arrange
    user = User(email="cancelled@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Cancelled"))
    upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based))

    # Act
    updated = upsert_trigger(
        db_session, user.id, folder.id,
        TriggerUpsert(type=TriggerType.time_based, state=TriggerState.cancelled)
    )

    # Assert
    assert updated.state == TriggerState.cancelled


@pytest.mark.unit
@pytest.mark.folders
def test_trigger_state_lifecycle(db_session):
    """
    Test #579: Trigger can transition through all states

    Validates state machine: configured -> scheduled -> fired.
    """
    # Arrange
    user = User(email="lifecycle@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    folder = create_folder(db_session, user.id, FolderCreate(name="Lifecycle"))

    # Act & Assert - configured
    trigger = upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based))
    assert trigger.state == TriggerState.configured

    # scheduled
    trigger = upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based, state=TriggerState.scheduled))
    assert trigger.state == TriggerState.scheduled

    # fired
    trigger = upsert_trigger(db_session, user.id, folder.id, TriggerUpsert(type=TriggerType.time_based, state=TriggerState.fired))
    assert trigger.state == TriggerState.fired
