# app/schemas/releases.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ReleaseItemOut(BaseModel):
    id: int
    title: str
    urls: List[str] = []
    meta: Dict[str, Any] = {}
    updated_at: Optional[str] = None  # ISO string
