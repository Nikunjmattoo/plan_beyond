# schemas/verification.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class VerificationMethod(str, Enum):
    document = "document"
    video = "video"
    referral = "referral"
    other = "other"

class VerificationStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class IdentityVerification(BaseModel):
    id: int
    user_id: int
    method: VerificationMethod
    document_type: Optional[str] = None
    document_ref: Optional[str] = None
    status: VerificationStatus = VerificationStatus.pending
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
