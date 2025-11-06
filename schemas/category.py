# app/schemas/category.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.models.enums import EventType

class CategoryMasterCreate(BaseModel):
    code: str
    name: str
    sort_index: Optional[int] = None
    icon: Optional[str] = None   # NEW

class CategoryMasterUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    sort_index: Optional[int] = None
    icon: Optional[str] = None   # NEW

class CategoryMasterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    sort_index: int
    icon: Optional[str] = None   # NEW

class SectionMasterCreate(BaseModel):
    code: str
    name: str
    sort_index: Optional[int] = None
    file_import: bool = False  # NEW

class SectionMasterUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    sort_index: Optional[int] = None
    file_import: Optional[bool] = None  # NEW

class SectionMasterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    code: str
    name: str
    sort_index: int
    file_import: bool  # NEW

# user adoption
class UserCategoryCreate(BaseModel):
    category_id: int
    event_type: EventType = EventType.after_death

class UserCategoryResponse(BaseModel):
    # model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    event_type: EventType

class UserCategorySectionCreate(BaseModel):
    section_master_id: int

class UserCategorySectionResponse(BaseModel):
    # model_config = ConfigDict(from_attributes=True)
    id: int
    user_category_id: int
    section_master_id: int
