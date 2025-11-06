from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime

# --- Catalog out ---
class StepOptionOut(BaseModel):
    id: int
    label: str
    value: str
    display_order: int
    meta: Optional[Dict[str, Any]] = None
    children: Optional[List["StepOptionOut"]] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

StepOptionOut.model_rebuild()

class FormStepOut(BaseModel):
    id: int
    section_master_id: int
    step_name: str
    question_id: Optional[str]
    title: str
    top_one_liner: Optional[str]
    bottom_one_line: Optional[str]
    display_order: int
    type: str
    nested: bool
    validation: bool
    mandatory: bool
    skippable: bool
    eligible_reminder: bool
    privacy_nudge: bool
    privacy_liner: Optional[str]
    config: Optional[dict]
    options: List[StepOptionOut] = []

    class Config:
        from_attributes = True

class StepsCatalogOut(BaseModel):
    category_id: int
    section_id: int
    section_name: str
    steps: List[FormStepOut]

# --- Save/get answers ---
class AnswerItem(BaseModel):
    step_id: int
    value: Any  # validated server-side based on step.type
    wants_reminder: Optional[bool] = None

class SaveSectionAnswersIn(BaseModel):
    category_id: int
    section_id: int
    progress_id: Optional[int] = None 
    record_key: Optional[str] = None
    answers_kv: Optional[Dict[str, Any]] = None
    answers: Optional[List[AnswerItem]] = None
    section_photo_url: Optional[str] = None
    reminders_kv: Optional[Dict[str, bool]] = None
    display_name: Optional[str] = None

class SavedSectionOut(BaseModel):
    category_id: int
    section_id: int
    progress_id: int
    saved_at: datetime
    submitted_at: Optional[datetime] = None
    section_photo_url: Optional[str] = None
    answers_kv: Dict[str, Any]
    reminders_kv: Dict[str, bool] = Field(default_factory=dict)
    display_name: Optional[str] = None

class UserReminderRow(BaseModel):
    progress_id: int
    category_id: int
    section_id: int
    section_name: str
    step_id: int
    question_id: Optional[str] = None
    step_title: Optional[str] = None
    enabled: bool
    value: Any = None
    saved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None

# ---------- NEW: Progress Leaf schemas ----------
class ProgressLeafCreate(BaseModel):
    contact_ids: List[int]  # bulk add

class ProgressLeafPatch(BaseModel):
    status: str  # "active" | "removed"

class ProgressLeafOut(BaseModel):
    id: int
    user_id: int
    category_id: int
    section_id: int
    progress_id: int
    contact_id: int
    status: str
    created_at: datetime
    updated_at: datetime
