"""
Reminder API Routes - FastAPI endpoints for reminder operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.dependencies import get_db, get_current_user_id
from app.controller.reminder import ReminderController
from app.schemas.reminder_schemas import (
    ReminderCreateRequest,
    ReminderResponse,
    ReminderListResponse,
    ReminderStatsResponse,
    ReminderAcknowledgeRequest,
    ReminderSnoozeRequest,
    ReminderCompleteRequest,
    ReminderActionResponse,
    ReminderFilterRequest,
    ReminderPreferenceResponse,
    ReminderPreferenceUpdateRequest,
    PendingCountResponse
)
from app.schemas.reminder_errors import (
    ReminderNotFoundException,
    ReminderAlreadyExistsException,
    ERROR_RESPONSES
)

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


# ==========================================
# CREATE REMINDER
# ==========================================

@router.post(
    "/",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_reminder(
    reminder_data: ReminderCreateRequest,
    current_user_id: str = Depends(get_current_user_id),  # Keep as string
    db: Session = Depends(get_db)
):
    """
    Create a new reminder for the current user.
    
    **Note:** Normally reminders are auto-created by the scheduler.
    This endpoint allows manual reminder creation.
    """
    controller = ReminderController(db)
    
    # Check for duplicates
    if controller.check_duplicate_reminder(
        user_id=current_user_id,
        vault_file_id=reminder_data.vault_file_id,
        field_name=reminder_data.field_name,
        reminder_date=reminder_data.reminder_date
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reminder already exists for this file and date"
        )
    
    reminder = controller.create_reminder(current_user_id, reminder_data)
    return ReminderResponse.model_validate(reminder)


# ==========================================
# LIST REMINDERS
# ==========================================

@router.get(
    "/",
    response_model=ReminderListResponse
)
async def list_reminders(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    urgency_level: Optional[str] = Query(None, description="Filter by urgency"),
    vault_file_id: Optional[str] = Query(None, description="Filter by vault file"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user_id),  # Keep as string
    db: Session = Depends(get_db)
):
    """
    List all reminders for current user with optional filters.
    
    Returns list of reminders sorted by date and urgency.
    """
    controller = ReminderController(db)
    
    # Build filters
    filters = ReminderFilterRequest(
        status=status_filter,
        category=category,
        urgency_level=urgency_level,
        vault_file_id=vault_file_id
    )
    
    reminders = controller.list_reminders(
        user_id=current_user_id,
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    counts = controller.get_pending_count(current_user_id)
    
    return ReminderListResponse(
        reminders=[ReminderResponse.model_validate(r) for r in reminders],
        total=len(reminders),
        pending_count=counts['pending_count'],
        critical_count=counts['critical_count']
    )


# ==========================================
# GET PENDING COUNT (FOR BADGE)
# ==========================================

@router.get(
    "/pending-count",
    response_model=PendingCountResponse
)
async def get_pending_count(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get count of pending reminders for badge display.
    
    Returns count of pending and critical reminders.
    """
    controller = ReminderController(db)
    counts = controller.get_pending_count(current_user_id)
    
    return PendingCountResponse(**counts)


# ==========================================
# GET SINGLE REMINDER
# ==========================================

@router.get(
    "/{reminder_id}",
    response_model=ReminderResponse
)
async def get_reminder(
    reminder_id: UUID,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get single reminder by ID"""
    controller = ReminderController(db)
    reminder = controller.get_reminder_by_id(reminder_id, current_user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return ReminderResponse.model_validate(reminder)


# ==========================================
# GET REMINDER STATS
# ==========================================

@router.get(
    "/stats/summary",
    response_model=ReminderStatsResponse
)
async def get_reminder_stats(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get reminder statistics for current user.
    
    Returns counts by status, category, urgency, and upcoming reminders.
    """
    controller = ReminderController(db)
    stats = controller.get_stats(current_user_id)
    
    return ReminderStatsResponse(**stats)


# ==========================================
# ACKNOWLEDGE REMINDER
# ==========================================

@router.patch(
    "/{reminder_id}/acknowledge",
    response_model=ReminderActionResponse
)
async def acknowledge_reminder(
    reminder_id: UUID,
    ack_data: ReminderAcknowledgeRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Mark reminder as acknowledged (user has seen it).
    """
    controller = ReminderController(db)
    reminder = controller.acknowledge_reminder(
        reminder_id,
        current_user_id,
        ack_data.acknowledged_by
    )
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return ReminderActionResponse(
        success=True,
        message="Reminder acknowledged",
        reminder_id=reminder_id
    )


# ==========================================
# SNOOZE REMINDER
# ==========================================

@router.patch(
    "/{reminder_id}/snooze",
    response_model=ReminderActionResponse
)
async def snooze_reminder(
    reminder_id: UUID,
    snooze_data: ReminderSnoozeRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Snooze reminder for specified hours.
    
    Reminder will reappear after snooze period ends.
    """
    controller = ReminderController(db)
    reminder = controller.snooze_reminder(
        reminder_id,
        current_user_id,
        snooze_data.snooze_hours
    )
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return ReminderActionResponse(
        success=True,
        message=f"Reminder snoozed for {snooze_data.snooze_hours} hours",
        reminder_id=reminder_id
    )


# ==========================================
# COMPLETE REMINDER
# ==========================================

@router.patch(
    "/{reminder_id}/complete",
    response_model=ReminderActionResponse
)
async def complete_reminder(
    reminder_id: UUID,
    complete_data: ReminderCompleteRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Mark reminder as completed with action taken.
    
    Example actions: 'paid', 'renewed', 'filed', 'scheduled'
    """
    controller = ReminderController(db)
    reminder = controller.complete_reminder(
        reminder_id,
        current_user_id,
        complete_data.completion_action
    )
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return ReminderActionResponse(
        success=True,
        message=f"Reminder marked as completed ({complete_data.completion_action})",
        reminder_id=reminder_id
    )


# ==========================================
# DISMISS REMINDER
# ==========================================

@router.patch(
    "/{reminder_id}/dismiss",
    response_model=ReminderActionResponse
)
async def dismiss_reminder(
    reminder_id: UUID,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Dismiss reminder (user doesn't want to see it anymore).
    """
    controller = ReminderController(db)
    reminder = controller.dismiss_reminder(reminder_id, current_user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return ReminderActionResponse(
        success=True,
        message="Reminder dismissed",
        reminder_id=reminder_id
    )


# ==========================================
# DELETE REMINDER
# ==========================================

@router.delete(
    "/{reminder_id}",
    response_model=ReminderActionResponse
)
async def delete_reminder(
    reminder_id: UUID,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Permanently delete reminder.
    """
    controller = ReminderController(db)
    success = controller.delete_reminder(reminder_id, current_user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return ReminderActionResponse(
        success=True,
        message="Reminder deleted",
        reminder_id=reminder_id
    )


# ==========================================
# GET USER PREFERENCES
# ==========================================

@router.get(
    "/preferences/me",
    response_model=ReminderPreferenceResponse
)
async def get_user_preferences(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current user's reminder preferences.
    
    Creates default preferences if they don't exist.
    """
    controller = ReminderController(db)
    preferences = controller.get_user_preferences(current_user_id)
    
    return ReminderPreferenceResponse.model_validate(preferences)


# ==========================================
# UPDATE USER PREFERENCES
# ==========================================

@router.patch(
    "/preferences/me",
    response_model=ReminderPreferenceResponse
)
async def update_user_preferences(
    updates: ReminderPreferenceUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update current user's reminder preferences.
    
    Only provided fields will be updated.
    """
    controller = ReminderController(db)
    preferences = controller.update_preferences(current_user_id, updates)
    
    return ReminderPreferenceResponse.model_validate(preferences)