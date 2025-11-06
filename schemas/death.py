from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AdminSoftRetract(BaseModel):
    reason: Optional[str] = None

class SoftDeathRequest(BaseModel):
    root_user_id: int
    message: Optional[str] = None
    media_ids: Optional[List[int]] = None
    audience_config: Optional[dict] = None

class HardDeathRequest(BaseModel):
    root_user_id: int
    evidence_file_id: int
    note: Optional[str] = None
    also_broadcast: Optional[bool] = False

class ContestCreate(BaseModel):
    reason: str
    evidence_file_id: Optional[int] = None

class AdminHardDecision(BaseModel):
    decision: str  # "accepted" | "rejected"
    notes: Optional[str] = None

class AdminDisputeDecision(BaseModel):
    decision: str  # "uphold_rollback" | "dismiss"
    notes: Optional[str] = None

# ---------- Responses ----------
class DeathDeclarationResponse(BaseModel):
    id: int
    root_user_id: int
    type: str
    state: str
    message: Optional[str] = None
    evidence_file_id: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ContestResponse(BaseModel):
    id: int
    declaration_id: int
    status: str
    decided_at: Optional[datetime] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True
