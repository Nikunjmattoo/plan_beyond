# app/schemas/contact.py
from pydantic import BaseModel, model_validator, ConfigDict, field_serializer
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile

class ContactBase(BaseModel):
    # Personal Information
    title: Optional[str] = None                      # ← NEW
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    local_name: Optional[str] = None
    contact_image: Optional[str] = None
    company: Optional[str] = None
    job_type: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    relation: Optional[str] = None

    # Contact Information
    phone_numbers: List[str] = []
    whatsapp_numbers: List[str] = []
    emails: List[str] = []

    # Address Information
    flat_building_no: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    # Additional Information
    date_of_birth: Optional[str] = None
    anniversary: Optional[str] = None
    notes: Optional[str] = None

    # UI Preference Flags
    share_by_whatsapp: Optional[bool] = False
    share_by_sms: Optional[bool] = False
    share_by_email: Optional[bool] = False

    # Storage field (DB)
    share_after_death: Optional[bool] = True
    is_emergency_contact: Optional[bool] = False

    # Frontend field (alias that maps to share_after_death)
    release_on_pass: Optional[bool] = None

    # Pydantic v2 validator: requireds + map release_on_pass -> share_after_death
    @model_validator(mode='before')
    def check_and_map(cls, values):
        # support both dict and model instance
        if isinstance(values, dict):
            first_name = values.get('first_name')
            emails = values.get('emails', []) or []
            phones = values.get('phone_numbers', []) or []
            rop = values.get('release_on_pass', None)
            sad = values.get('share_after_death', None)
            # prefer release_on_pass if provided
            if rop is not None:
                values['share_after_death'] = bool(rop)
            elif sad is None:
                # default if neither given
                values['share_after_death'] = False
        else:
            first_name = getattr(values, 'first_name', None)
            emails = getattr(values, 'emails', []) or []
            phones = getattr(values, 'phone_numbers', []) or []
            rop = getattr(values, 'release_on_pass', None)
            sad = getattr(values, 'share_after_death', None)
            if rop is not None:
                setattr(values, 'share_after_death', bool(rop))
            elif sad is None:
                setattr(values, 'share_after_death', False)

        if not first_name:
            raise ValueError("first_name is required")
        if not emails and not phones:
            raise ValueError("At least one of emails or phone_numbers must be provided")
        return values

    # Always serialize release_on_pass from share_after_death for the frontend
    @field_serializer('release_on_pass', when_used='always')
    def ser_release_on_pass(self, v, info):
        # v is the field value if present; fall back to share_after_death
        sad = getattr(self, 'share_after_death', False)
        return bool(sad)

class ContactCreate(ContactBase):
    contact_image: Optional[str] = None
    contact_image_file: Optional[UploadFile] = None  # <-- NEW

class MemoryCollectionLite(BaseModel):
    id: int
    name: str
class ContactResponse(ContactBase):
    id: int
    owner_user_id: int
    linked_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    memory_collections_data: List[MemoryCollectionLite] = [] 
    
