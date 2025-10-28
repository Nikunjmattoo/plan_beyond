from pydantic import BaseModel, field_validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from app.models.enums import EventType, AssignmentRole, FolderStatus, BranchInviteStatus

class MemoryAssignmentIn(BaseModel):
    contact_id: int
    role: AssignmentRole

class MemoryFileAttach(BaseModel):
    file_id: Optional[int] = None
    app_url: Optional[HttpUrl] = None
    title: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None

    @field_validator("app_url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return v or None

    @field_validator("file_id", "app_url")
    @classmethod
    def require_one_of(cls, v, info):
        data = info.data
        if (data.get("file_id") is None) and (data.get("app_url") is None):
            raise ValueError("Provide either file_id or app_url")
        return v

class MemoryFileInline(BaseModel):
    app_url: str
    title: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None

class MemoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_type: EventType = EventType.event
    scheduled_at: Optional[datetime] = None
    event_label: Optional[str] = None
    assignments: List[MemoryAssignmentIn] = []
    files: List[MemoryFileInline] = []

    @field_validator("scheduled_at")
    @classmethod
    def validate_time_requirement(cls, v, info):
        data = info.data
        if data.get("event_type") == EventType.time and v is None:
            raise ValueError("scheduled_at is required when event_type is 'time'")
        return v

    @field_validator("event_label", mode="before")
    @classmethod
    def empty_event_label_to_none(cls, v):
        if v is None: return None
        v = str(v).strip()
        return v if v else None

    @field_validator("event_label")
    @classmethod
    def validate_event_requirement(cls, v, info):
        data = info.data
        # if data.get("event_type") == EventType.event and not v:
        #     raise ValueError("event_label is required when event_type is 'event'")
        return v

class MemoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    scheduled_at: Optional[datetime] = None
    event_label: Optional[str] = None
    assignments: Optional[List["MemoryAssignmentIn"]] = None
    files: Optional[List[MemoryFileInline]] = None

class MemoryAssignmentOut(BaseModel):
    id: int
    contact_id: int
    role: AssignmentRole
    # ✅ NEW: branch invite lifecycle
    invite_status: Optional[BranchInviteStatus] = None
    invited_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MemoryFileOut(BaseModel):
    id: int
    file_id: Optional[int] = None
    app_url: Optional[str] = None
    title: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    class Config:
        from_attributes = True

class MemoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    event_type: EventType
    scheduled_at: Optional[datetime]
    event_label: Optional[str] = None
    is_armed: bool
    status: FolderStatus
    files: Optional[List[MemoryFileOut]] = None
    assignments: Optional[List[MemoryAssignmentOut]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TriggerIn(BaseModel):
    memory_file_id: int
