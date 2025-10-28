from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FileCreate(BaseModel):
    folder_id: int
    name: str

class FileResponse(BaseModel):
    id: int
    folder_id: int
    name: str
    storage_ref: str
    hash_sha256: str
    size: int
    mime_type: Optional[str] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FileUpdate(BaseModel):
    name: Optional[str] = None
