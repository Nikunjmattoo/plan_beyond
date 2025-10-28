from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import enum

class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    declined = "declined"
    removed = "removed"

class LeafRole(str, enum.Enum):
    leaf = "leaf"
    fallback_leaf = "fallback_leaf"

class TriggerType(str, enum.Enum):
    time_based = "time_based"
    event_based = "event_based"

class TriggerState(str, enum.Enum):
    configured = "configured"
    scheduled = "scheduled"
    fired = "fired"
    cancelled = "cancelled"

class FolderComputedStatus(str, enum.Enum):
    complete = "complete"
    incomplete = "incomplete"

# -------- FOLDER --------

class FolderCreate(BaseModel):
    name: str

class FolderUpdate(BaseModel):
    name: Optional[str] = None

class FolderResponse(BaseModel):
    id: int
    name: str
    status: FolderComputedStatus
    missing: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# -------- BRANCH --------

class BranchCreate(BaseModel):
    contact_id: int
    status: AssignmentStatus = AssignmentStatus.pending
    accepted_at: Optional[datetime] = None

class BranchUpdate(BaseModel):
    status: Optional[AssignmentStatus] = None
    accepted_at: Optional[datetime] = None

class BranchResponse(BaseModel):
    id: int
    folder_id: int
    contact_id: int
    status: AssignmentStatus
    accepted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# -------- LEAF --------

class LeafCreate(BaseModel):
    contact_id: int
    role: LeafRole = LeafRole.leaf
    status: AssignmentStatus = AssignmentStatus.pending
    accepted_at: Optional[datetime] = None

class LeafUpdate(BaseModel):
    role: Optional[LeafRole] = None
    status: Optional[AssignmentStatus] = None
    accepted_at: Optional[datetime] = None

class LeafResponse(BaseModel):
    id: int
    folder_id: int
    contact_id: int
    role: LeafRole
    status: AssignmentStatus
    accepted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# -------- TRIGGER --------

class TriggerUpsert(BaseModel):
    type: TriggerType
    time_at: Optional[datetime] = None
    timezone: Optional[str] = None
    event_label: Optional[str] = None
    state: TriggerState = TriggerState.configured

class TriggerResponse(BaseModel):
    id: int
    folder_id: int
    type: TriggerType
    time_at: Optional[datetime]
    timezone: Optional[str]
    event_label: Optional[str]
    state: TriggerState
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True