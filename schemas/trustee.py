from pydantic import BaseModel
from typing import Optional
from app.models.enums import TrusteeStatus, ApprovalStatus
from datetime import date, datetime

class TrusteeBase(BaseModel):
    contact_id: int

class TrusteeInvite(TrusteeBase):
    is_primary: bool = False

class TrusteeOut(BaseModel):
    id: int
    contact_id: int
    status: TrusteeStatus
    is_primary: bool
    invited_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class DeathStatusOut(BaseModel):
    death_declared: bool
    approvals: list[int]   # trustee_ids who approved

class DeathApproveIn(BaseModel):
    trustee_id: int
    action: ApprovalStatus  # approved or retracted
