"""
Pydantic schemas for Reminder API - Request/Response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID


# ==========================================
# REMINDER SCHEMAS
# ==========================================

class ReminderBase(BaseModel):
    """Base reminder fields"""
    vault_file_id: str = Field(..., max_length=64)
    field_name: str = Field(..., max_length=100)
    reminder_category: str = Field(..., max_length=50)
    trigger_date: date
    reminder_date: date
    title: str = Field(..., max_length=200)
    message: str
    urgency_level: str = Field(..., max_length=20)
    
    @validator('reminder_category')
    def validate_category(cls, v):
        valid_categories = [
            'expiry', 'recurring_payment', 'maturity', 
            'renewal', 'health', 'custom'
        ]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v
    
    @validator('urgency_level')
    def validate_urgency(cls, v):
        valid_urgency = ['info', 'normal', 'important', 'critical']
        if v not in valid_urgency:
            raise ValueError(f"Urgency must be one of: {', '.join(valid_urgency)}")
        return v


class ReminderCreateRequest(ReminderBase):
    """Create reminder request"""
    pass


class ReminderResponse(ReminderBase):
    """Reminder response"""
    id: UUID
    user_id: int
    status: str
    
    # Delivery tracking
    email_sent: bool
    email_sent_at: Optional[datetime]
    email_opened: bool
    email_clicked: bool
    
    # User actions
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    completed_at: Optional[datetime]
    completion_action: Optional[str]
    dismissed_at: Optional[datetime]
    snoozed_at: Optional[datetime]
    snoozed_until: Optional[datetime]
    snooze_count: int
    
    # Escalation
    escalation_level: int
    last_escalated_at: Optional[datetime]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReminderListResponse(BaseModel):
    """List of reminders"""
    reminders: List[ReminderResponse]
    total: int
    pending_count: int
    critical_count: int


class ReminderStatsResponse(BaseModel):
    """Reminder statistics for user"""
    total_reminders: int
    pending: int
    sent: int
    acknowledged: int
    completed: int
    dismissed: int
    snoozed: int
    
    by_category: dict
    by_urgency: dict
    upcoming_7_days: int
    upcoming_30_days: int


# ==========================================
# ACTION SCHEMAS
# ==========================================

class ReminderAcknowledgeRequest(BaseModel):
    """Acknowledge reminder"""
    acknowledged_by: str = Field(default="user", max_length=20)


class ReminderSnoozeRequest(BaseModel):
    """Snooze reminder"""
    snooze_hours: int = Field(..., ge=1, le=168, description="Hours to snooze (1-168)")


class ReminderCompleteRequest(BaseModel):
    """Complete reminder"""
    completion_action: str = Field(..., max_length=50, description="Action taken (e.g., 'paid', 'renewed', 'filed')")


class ReminderActionResponse(BaseModel):
    """Generic action response"""
    success: bool
    message: str
    reminder_id: UUID


# ==========================================
# FILTER SCHEMAS
# ==========================================

class ReminderFilterRequest(BaseModel):
    """Filter reminders"""
    status: Optional[str] = None
    category: Optional[str] = None
    urgency_level: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    vault_file_id: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is None:
            return v
        valid_status = ['pending', 'sent', 'acknowledged', 'completed', 'dismissed', 'snoozed']
        if v not in valid_status:
            raise ValueError(f"Status must be one of: {', '.join(valid_status)}")
        return v


# ==========================================
# PREFERENCE SCHEMAS
# ==========================================

class ReminderPreferenceResponse(BaseModel):
    """User reminder preferences"""
    user_id: int
    
    # Expiry reminders
    expiry_in_app: bool
    expiry_email: bool
    expiry_sms: bool
    expiry_push: bool
    
    # Payment reminders
    recurring_payment_in_app: bool
    recurring_payment_email: bool
    recurring_payment_sms: bool
    recurring_payment_push: bool
    
    # Maturity reminders
    maturity_in_app: bool
    maturity_email: bool
    maturity_sms: bool
    maturity_push: bool
    
    # Renewal reminders
    renewal_in_app: bool
    renewal_email: bool
    renewal_sms: bool
    renewal_push: bool
    
    # Health reminders
    health_in_app: bool
    health_email: bool
    health_sms: bool
    health_push: bool
    
    # Custom reminders
    custom_in_app: bool
    custom_email: bool
    custom_sms: bool
    custom_push: bool
    
    # Timing preferences
    preferred_time: time
    timezone: str
    quiet_hours_start: time
    quiet_hours_end: time
    
    # Grouping
    group_similar_reminders: bool
    send_daily_digest: bool
    send_weekly_summary: bool
    
    # Remove these two lines - they're causing the error:
    # created_at: datetime
    # updated_at: datetime
    
    class Config:
        from_attributes = True

class ReminderPreferenceUpdateRequest(BaseModel):
    """Update reminder preferences"""
    # Expiry reminders
    expiry_in_app: Optional[bool] = None
    expiry_email: Optional[bool] = None
    expiry_sms: Optional[bool] = None
    expiry_push: Optional[bool] = None
    
    # Payment reminders
    recurring_payment_in_app: Optional[bool] = None
    recurring_payment_email: Optional[bool] = None
    recurring_payment_sms: Optional[bool] = None
    recurring_payment_push: Optional[bool] = None
    
    # Maturity reminders
    maturity_in_app: Optional[bool] = None
    maturity_email: Optional[bool] = None
    maturity_sms: Optional[bool] = None
    maturity_push: Optional[bool] = None
    
    # Renewal reminders
    renewal_in_app: Optional[bool] = None
    renewal_email: Optional[bool] = None
    renewal_sms: Optional[bool] = None
    renewal_push: Optional[bool] = None
    
    # Health reminders
    health_in_app: Optional[bool] = None
    health_email: Optional[bool] = None
    health_sms: Optional[bool] = None
    health_push: Optional[bool] = None
    
    # Custom reminders
    custom_in_app: Optional[bool] = None
    custom_email: Optional[bool] = None
    custom_sms: Optional[bool] = None
    custom_push: Optional[bool] = None
    
    # Timing preferences
    preferred_time: Optional[time] = None
    timezone: Optional[str] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    
    # Grouping
    group_similar_reminders: Optional[bool] = None
    send_daily_digest: Optional[bool] = None
    send_weekly_summary: Optional[bool] = None


class PendingCountResponse(BaseModel):
    """Pending reminders count for badge"""
    pending_count: int
    critical_count: int