from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ---- Admin (templates) ----

class SectionItemTemplateCreate(BaseModel):
    section_master_id: int
    code: str
    name: str
    icon: Optional[str] = None
    sort_index: int = 0
    is_recommended: bool = False
    is_pre_populated: bool = False

class SectionItemTemplateUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    icon: Optional[str] = None
    sort_index: Optional[int] = None
    is_recommended: Optional[bool] = None
    is_pre_populated: Optional[bool] = None

class SectionItemTemplateOut(BaseModel):
    id: int
    section_master_id: int
    code: str
    name: str
    icon: Optional[str]
    sort_index: int
    is_recommended: bool
    is_pre_populated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ---- User items ----

class UserSectionItemOut(BaseModel):
    id: int
    user_category_section_id: int
    template_id: Optional[int]
    title: str
    icon: Optional[str]
    sort_index: int
    is_pre_populated: bool
    is_recommended: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
