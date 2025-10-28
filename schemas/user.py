from datetime import date, datetime
from pydantic import BaseModel, validator
from typing import Optional
from enum import Enum

class UserStatus(str, Enum):
    unknown = "unknown"
    guest = "guest"
    verified = "verified"
    member = "member"

class CommunicationChannel(str, Enum):
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"

class VerificationMethod(str, Enum):
    document = "document"
    referral = "referral"
    other = "other"

class VerificationStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

def _at_least_16_years_old(d: Optional[date]) -> Optional[date]:
    """Return the date if >=16, else raise ValueError."""
    if d is None:
        return d
    today = date.today()
    # Compute the date 16 years ago (careful with leap years)
    try:
        sixteen_ago = d.replace(year=d.year + 16)  # will be compared to today
        # If their 16th birthday is in the future -> invalid
        if sixteen_ago > today:
            raise ValueError("User must be at least 16 years old.")
    except ValueError:
        # Fallback: if replacing year failed (e.g. Feb 29), compare year diff by hand
        year_diff = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        if year_diff < 16:
            raise ValueError("User must be at least 16 years old.")
    return d

class UserBase(BaseModel):
    
    display_name: str
    email: Optional[str] = None
    country_code: Optional[str] = None  # NEW
    phone: Optional[str] = None
    communication_channel: Optional[CommunicationChannel] = None
    title: Optional[str] = None   
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary: Optional[date] = None
    gender: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None

    @validator("phone")
    def normalize_phone(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("email")
    def normalize_email(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("country_code")
    def normalize_country_code(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v and not v.startswith("+"):
                v = f"+{v}"
        return v

    @validator("date_of_birth")
    def validate_min_age(cls, v):
        return _at_least_16_years_old(v)

    @validator("communication_channel", pre=True, always=True)
    def ensure_contact_exists(cls, v, values):
        email = values.get("email")
        phone = values.get("phone")
        if not email and not phone:
            raise ValueError("At least one of email or phone must be provided")
        return v

class UserCreate(UserBase):
    password: Optional[str] = None

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None  
    communication_channel: Optional[CommunicationChannel] = None
    password: Optional[str] = None

    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary: Optional[date] = None
    gender: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None

    @validator("phone")
    def normalize_phone(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("email")
    def normalize_email(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("country_code")
    def normalize_country_code(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v and not v.startswith("+"):
                v = f"+{v}"
        return v
    @validator("date_of_birth")
    def validate_min_age(cls, v):
        return _at_least_16_years_old(v)


class UserProfileResponse(BaseModel):
    # flat shape expected by your frontend
    id: int
    display_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None  # NEW
    communication_channel: Optional[CommunicationChannel] = None
    status: UserStatus
    created_at: datetime
    otp_verified: bool = False
    title: Optional[str] = None 
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary: Optional[date] = None
    gender: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class LoginCredentials(BaseModel):
    identifier: str
    password: Optional[str] = None

class OTPStart(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None  
    communication_channel: CommunicationChannel


class OTPVerify(BaseModel):
    user_id: int
    otp: str

# Admin OTP Schemas
class AdminOTPStart(BaseModel):
    email: str

class AdminOTPVerify(BaseModel):
    admin_id: int
    otp: str

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

class VerificationSubmit(BaseModel):
    method: VerificationMethod = VerificationMethod.document
    document_type: Optional[str] = None
    document_ref: Optional[str] = None
