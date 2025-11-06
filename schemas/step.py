from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime
import enum

class StepType(str, enum.Enum):
    list = "list"
    hierarchical = "hierarchical"
    single_select = "single_select"
    checklist = "checklist"
    open = "open"
    date_mm_yyyy = "date_mm_yyyy"
    date_dd_mm_yyyy = "date_dd_mm_yyyy"
    google_location = "google_location"
    photo = "photo"
    file_upload = "file_upload"

class ReminderType(str, enum.Enum):
    maturity = "maturity"
    recurring_payment = "recurring_payment"
    expiry = "expiry"

class WidgetType(str, enum.Enum):
    # keep it flexible but constrained to what the frontend uses
    radio = "radio"
    checkbox = "checkbox"
    dropdown = "dropdown"
    cascader = "cascader"
    contact = "contact"
    category = "category"
    section = "section"

# -------- Options --------
class StepOptionCreate(BaseModel):
    label: str
    value: str
    display_order: Optional[int] = None
    parent_value: Optional[str] = None
    meta: Optional[dict[str, Any]] = None

class StepOptionUpdate(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None
    display_order: Optional[int] = None
    parent_option_id: Optional[int] = None
    meta: Optional[dict[str, Any]] = None

class StepOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_id: int
    label: str
    value: str
    display_order: int
    parent_option_id: Optional[int] = None
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

# -------- Steps --------
class StepCreate(BaseModel):
    step_name: str
    question_id: Optional[str] = None
    title: str
    top_one_liner: Optional[str] = None
    bottom_one_line: Optional[str] = None
    display_order: Optional[int] = None

    type: StepType

    # behaviour (kept)
    validation: bool = False
    mandatory: bool = False
    eligible_reminder: bool = False

    # privacy (kept)
    privacy_nudge: bool = False
    privacy_liner: Optional[str] = None

    # NEW first-class fields
    widget: Optional[WidgetType] = None
    label: Optional[Dict[str, Any]] = None  # e.g. {"default": "Account number"}

    pii: Optional[bool] = None
    pii_note: Optional[str] = None
    format: Optional[str] = None
    reminder_after_days: Optional[int] = None
    reminder_type: Optional[ReminderType] = None
    validation_pattern: Optional[str] = None

    # free-form config (legacy / extras only)
    config: Optional[dict[str, Any]] = None

    # Optional initial options
    options: Optional[List[StepOptionCreate]] = None

class StepUpdate(BaseModel):
    step_name: Optional[str] = None
    question_id: Optional[str] = None
    title: Optional[str] = None
    top_one_liner: Optional[str] = None
    bottom_one_line: Optional[str] = None
    display_order: Optional[int] = None

    type: Optional[StepType] = None

    validation: Optional[bool] = None
    mandatory: Optional[bool] = None
    eligible_reminder: Optional[bool] = None

    privacy_nudge: Optional[bool] = None
    privacy_liner: Optional[str] = None

    widget: Optional[WidgetType] = None
    label: Optional[Dict[str, Any]] = None

    pii: Optional[bool] = None
    pii_note: Optional[str] = None
    format: Optional[str] = None
    reminder_after_days: Optional[int] = None
    reminder_type: Optional[ReminderType] = None
    validation_pattern: Optional[str] = None

    config: Optional[dict[str, Any]] = None

class StepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_master_id: int
    step_name: str
    question_id: Optional[str]
    title: str
    top_one_liner: Optional[str]
    bottom_one_line: Optional[str]
    display_order: int
    type: StepType

    validation: bool
    mandatory: bool
    eligible_reminder: bool

    privacy_nudge: bool
    privacy_liner: Optional[str]

    # NEW first-class fields
    widget: Optional[WidgetType]
    label: Optional[Dict[str, Any]]

    pii: Optional[bool]
    pii_note: Optional[str]
    format: Optional[str]
    reminder_after_days: Optional[int]
    reminder_type: Optional[ReminderType]
    validation_pattern: Optional[str]

    config: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    options: List[StepOptionResponse] = []
