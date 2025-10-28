# app/schemas/messages.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.enums import EventType, AssignmentRole, BranchInviteStatus, FolderStatus

class MsgAssignmentIn(BaseModel):
    contact_id: int
    role: AssignmentRole

class MsgCreate(BaseModel):
    name: str = Field(..., min_length=1)
    message_text: str = Field("", description="Plain text; stored as data:text/plain URL")

    event_type: EventType = EventType.event
    scheduled_at: Optional[datetime] = None
    event_label: Optional[str] = None

    assignments: List[MsgAssignmentIn] = []

    @field_validator("scheduled_at")
    @classmethod
    def require_when_time(cls, v, info):
        if info.data.get("event_type") == EventType.time and v is None:
            raise ValueError("scheduled_at is required when event_type is 'time'")
        return v

class MsgUpdate(BaseModel):
    name: Optional[str] = None
    message_text: Optional[str] = None
    event_type: Optional[EventType] = None
    scheduled_at: Optional[datetime] = None
    event_label: Optional[str] = None
    assignments: Optional[List[MsgAssignmentIn]] = None

class MsgAssignmentOut(BaseModel):
    id: int
    contact_id: int
    role: AssignmentRole
    invite_status: Optional[BranchInviteStatus] = None
    invited_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MsgFileOut(BaseModel):
    id: int
    app_url: Optional[str] = None
    title: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None

    class Config:
        from_attributes = True

class MsgOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    event_type: EventType
    scheduled_at: Optional[datetime] = None
    event_label: Optional[str] = None
    is_armed: bool
    status: FolderStatus
    files: Optional[List[MsgFileOut]] = None
    assignments: Optional[List[MsgAssignmentOut]] = None
    message_text: Optional[str] = None   # convenience for detail view

    class Config:
        from_attributes = True
