# app/schemas/relationship.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import enum

class TodoStatus(str, enum.Enum):
    actionable = "actionable"      # event-based & not fired/cancelled → has CTA
    informational = "informational" # time-based visibility only
    done = "done"                  # fired
    cancelled = "cancelled"        # cancelled

class BranchTodoItem(BaseModel):
    # stable id for the UI (folder+trigger)
    todo_id: str

    folder_id: int
    folder_name: str
    root_user_display_name: str

    trigger_type: str
    trigger_state: str

    # UI copy
    title: str
    subtitle: Optional[str] = None

    # scheduling context (time-based)
    next_at: Optional[datetime] = None
    timezone: Optional[str] = None

    status: TodoStatus
    cta_label: Optional[str] = None
    can_mark_happened: bool = False

class BranchTodoSummary(BaseModel):
    actionable_count: int
    informational_count: int
    done_count: int
    cancelled_count: int

class RequestStatus(str, enum.Enum):
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"
    revoked = "revoked"
    expired = "expired"

class RelationshipRequestCreate(BaseModel):
    contact_id: int
    sent_via: Optional[str] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None

class RelationshipRequestResponse(BaseModel):
    id: int
    folder_id: int
    contact_id: int
    status: RequestStatus
    sent_via: Optional[str]
    message: Optional[str]
    expires_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    revoked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RelationshipRequestAccept(BaseModel):
    token: str

class RelationshipRequestReject(BaseModel):
    token: str
    reason: Optional[str] = None

class BranchResponsibilityItem(BaseModel):
    folder_id: int
    folder_name: str
    root_user_display_name: str
    trigger_type: str
    trigger_state: str
    time_at: Optional[datetime] = None
    timezone: Optional[str] = None
    event_label: Optional[str] = None
    is_actionable: bool
