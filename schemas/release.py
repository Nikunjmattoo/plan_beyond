
from pydantic import BaseModel
from typing import Literal, Optional, List
from app.models.enums import ReleaseScope, ReleaseReason

class ReleaseOut(BaseModel):
    id: int
    scope: ReleaseScope
    scope_id: int
    reason: ReleaseReason
    class Config:
        from_attributes = True
